# -*- coding: utf-8 -*-
"""
Created on Nov 22 09:57:29 2017

@author: Steinn Ymir Agustsson

    Copyright (C) 2018 Steinn Ymir Agustsson, Vladimir Grigorev

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import os, sys
import time
from PyQt5 import QtCore
import h5py

from instruments import generic
from utilities.qt import raise_Qerror
from utilities.misc import nested_for, iterate_ranges, parse_setting
from utilities.exceptions import RequirementError
from utilities.math import globalcounter


def main():
    import time
    from instruments.lockinamplifier import SR830
    from instruments.delaystage import DelayStage
    from instruments.cryostat import Cryostat
    time.sleep(2)
    exp = Experiment()
    lockin = exp.add_instrument('lockin', SR830())
    stage = exp.add_instrument('stage', DelayStage())
    cryo = exp.add_instrument('cryo', Cryostat())
    exp.print_setup()
    time.sleep(1)
    exp.create_file()
    exp.add_parameter_iteration(cryo, 'change_temperature', [10, 20, 30, 40, 50])
    exp.start_measurement()


class Experiment(QtCore.QObject):
    """ Experiment manager class.

    An object of this class is intended to control an experiment.

    This is done by adding to it instruments, via the :obj:add_instrument* method.

    A measurement session can be defined by adding parameter iterations.
    This is done by using the method `add_parameter_iteration`, which creates a
    tuple of 3 objects: the *instrument*, the *parameter* and *values*.
    **Instrument**: is an instance of the instrument which will be used to
    control this parameter.
    **parameter** is the name under which this parameter can be found in the
    instrument object instance
    **value** is a tuple or list of values. These are in order the values at
    which this parameter will be set. Each value will generate a measurement loop.

    This measurement loop can consist of multiple parameter iterations, meaning
    a measurement session can perform a measurement iterating over multiple
    parameters, resulting in n-dimensional measurements.

    Examples:
        # TODO: write some nice examples.
    Signals:
        finished (): at end of the scan. Bounced from worker.
        newData (): emitted at each measurement point.Bounced from worker.
            together with scan current_step information.
        stateChanged (str): emitted when the state of the worker changes.
            Allowed state values are defined in STATE_VALUES. Bounced from worker.

    """
    __verbose = parse_setting('general', 'verbose')
    __TYPE = 'generic'
    # Signals
    finished = QtCore.pyqtSignal(dict)
    newData = QtCore.pyqtSignal(dict)
    progressChanged = QtCore.pyqtSignal(float)
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, file=None, **kwargs):
        """ Create an instance of the Experiment

        This is initialized by creating adding all the passed arguments as
        instrument instances, and creates a list of names of them in
        self.instrument_list.
        Then, all methods which can be used to measure some quantity and all
        parameters which can be set for each instruments are collected in
        self.measurable_methods and self.parameters respectively.

        self.measurable_methods is therefore a list of methods which can be
        directly called. These methods must have a test on the parent
        instrument being connected, or might fail.

        the class attribute *parameters* is a dictionary, where keys are the
        names of the instruments to which they belong. Each value is then a
        dictionary containing the name of the parameter as keys and a pointer
        to the parameter instance in the value.

        Args:
            file (:obj:str): file where to store experiment data. Defaults to
                :obj:None. If an existing file is passed, all settings stored
                in such file are loaded to the instance.
            kwargs (:obj:generic.Instrument): The names ofn given keyword
                arguments will be the specific name of the instrument
                (example: probe_stage) and the value must be an instance of the
                specific instrument (example: delaystage.NewportXPS)

        """
        super().__init__()

        self.instrument_list = []
        self.parameters = {}
        self.required_instruments = None

        self.measurement_file = file
        self.measurement_name = 'unknown measurement ' + time.asctime().replace(':', '-')
        self.measurement_parameters = []
        self.measurement_settings = {}
        self.base_instruments = []
        # define which worker to use:
        self.worker = None

        if self.measurement_file is not None:
            self.load_settings_from_h5()
        for key, val in kwargs.items():
            try:
                self.add_instrument(key, val)
            except AssertionError:
                setattr(self, key, val)
        self.get_parameters()

    def add_parameter_iteration(self, name,unit,instrument, method, values):
        """ adds a measurement loop to the measurement plan.

        Args:
            instrument (generic.Instrument): instance of an instrument.
            parameter (str): method to be called to change the intended quantity
            values(:obj:list or :obj:tuple): list of parameters to be set, in
                the order in which they will be iterated.
        Raises:
            AssertionError: when any of the types are not respected.
        """
        assert isinstance(name,str), 'name must be a string'
        assert isinstance(unit,str), 'unit must be a string'
        assert isinstance(instrument, generic.Instrument), ' instrumnet must be instance of generic.Instrument'
        assert isinstance(method, str) and hasattr(instrument, method), 'method should be a string representing the name of a method of the instrumnet class'
        assert isinstance(values, (list, tuple)), 'values should be list or tuple of numbers.'
        if self.__verbose:
            print('Added parameter iteration:\n\t- Instrument: {}\n\t- Method: {}\n\t- Values: {}'.format(instrument,
                                                                                                          method,
                                                                                                          values))
        self.measurement_parameters.append((name,unit,instrument, method, values))

    def check_requirements(self):
        """ check if the minimum requirements are fulfilled.

        Raises:
            RequirementError: if any requirement is not fulfilled.
        """
        try:
            missing = [x for x in self.required_instruments]
            for instrument in self.instrument_list:

                for i, inst_type in enumerate(self.required_instruments):
                    if isinstance(getattr(self, instrument), inst_type):
                        if self.__verbose: print('found {} as {}'.format(instrument, inst_type))
                        self.base_instruments.append((instrument, getattr(self, instrument)))
                        missing.remove(inst_type)
                        break
            if len(missing) > 0:
                raise RequirementError('no instrument of type {} present.'.format(missing))
            elif not os.path.isfile(self.measurement_file):
                raise FileNotFoundError('no File defined for this measurement.')
            else:
                print('all requrements met. Good to go!')
        except TypeError:
            print('No requirements set. Nothing to check!')

    def get_parameters(self):
        """ Find all parameters which can be set and write them to a dictionary in self.parameters"""
        if self.__verbose: print('Retreaving parameters\n')
        for instrument in self.instrument_list:
            instrument_instance = getattr(self, instrument)
            for attr, val in instrument_instance.__dict__.items():
                if isinstance(getattr(instrument_instance, attr), generic.Parameter):
                    if self.__verbose: print('\t- Found {} in {}'.format(attr, instrument))
                    self.parameters[instrument][attr] = getattr(instrument_instance, attr)

    def add_instrument(self, name, model, return_=True):
        """ Add an instrument to the experimental setup.

        adds as a class attribute an instance of a given model of an instrument,
        with a name of choice.

        This is intended to use by calling ExperimentalSetup.<instrument name>

        : parameters :
            name: str
                name to give to this specific instrument
            model: Instrument
                instance of the class corresponding to the model of this instrument
        """
        assert isinstance(model, generic.Instrument), '{} is not a recognized instrument type'.format(model)
        setattr(self, name, model)
        self.instrument_list.append(name)
        if self.__verbose: print('Added {} as instance of {}'.format(name, model))
        if return_: return getattr(self, name)

    def print_setup(self):
        if len(self.instrument_list) == 0:
            print('No instruments loaded.')
        else:
            for name in self.instrument_list:
                print('{}: type:{}'.format(name, type(getattr(self, name))))

    def connect_all(self, *args):
        """ Connect to the instruments.

        Connects to all instruments, unless the name of one or multiple specific
        isntruments is passed, in which case it only connects to these.

        :parameters:
            *args: str
                name of the instrument(s) to be connected
        """
        if len(args) == 0:
            connect_list = tuple(self.instrument_list)
        else:
            connect_list = args
        for name in connect_list:
            getattr(self, name).connect()
            if self.__verbose: print('Connected {}'.format(name))

    def disconnect_all(self, *args):
        """ Connect to the instruments.

        Connects to all instruments, unless the name of one or multiple specific
        instruments is passed, in which case it only connects to these.

        :parameters:
            *args: str
                name of the instrument(s) to be connected
        """
        if len(args) == 0:
            disconnect_list = tuple(self.instrument_list)
        else:
            disconnect_list = args
        for name in disconnect_list:
            assert hasattr(self, name), 'No instrument named {} found.'.format(name)
            getattr(self, name).disconnect()
            if self.__verbose: print('Disconnected {}'.format(name))

    def clear_instrument_list(self):
        """ Remove all instruments from the current instance."""
        self.disconnect_all()
        for inst in self.instrument_list:
            delattr(self, inst)
            if self.__verbose: print('Removed {} from available instruments'.format(inst))
        self.instrument_list = []

    def initialize_experiment(self):
        """ Initialize experiment.

        Check basic requirements, test any needed options or settings.
        This method is experiment type dependent and should be reimplemented in
        each subclass of Experiment.
        """
        self.check_requirements()
        # raise NotImplementedError('no initialization method in this experiment (sub)class')

    def start_measurement(self):
        """ start a measurement"""
        self.check_requirements()

        self.scan_thread = QtCore.QThread()
        self.w = self.worker(self.measurement_file,
                             self.base_instruments,
                             self.measurement_parameters,
                             **self.measurement_settings)

        self.w.finished.connect(self.on_finished)
        self.w.newData.connect(self.on_newData)
        self.w.progressChanged[float].connect(self.on_progressChanged)
        self.w.stateChanged[str].connect(self.on_stateChanged)

        if self.__verbose: print('initialized: moving to new thread')
        self.w.moveToThread(self.scan_thread)
        if self.__verbose: print('connecting')
        self.scan_thread.started.connect(self.w.work)
        if self.__verbose: print('starting')
        self.scan_thread.start()
        self.can_die=False
        while not self.can_die :
            time.sleep(2)
        if self.__verbose: print('wtf???')

    def create_file(self, name=None, dir=None, replace=True):
        """ Initialize a file for a measurement.

        :Structure:
            Each file will have 3 main groups (folders):
                **data**: where the dataframes will be stored
                **axes**: where the axes corresponding to the dataframes
                    dimensions will be stored
                **settings**: where the settings for each connected instruments
                    are saved.


        """
        if name is not None:
            self.measurement_name = name
        if dir is None:
            dir = parse_setting('paths', 'h5_data')
        filename = os.path.join(dir, self.measurement_name)
        filename += '.h5'
        self.measurement_file = filename
        if os.path.isfile(filename) and replace:
            raise NameError('name already exists, please change.')
        else:
            if self.__verbose: print('Created file {}'.format(filename))
            with h5py.File(filename, 'w', libver='latest') as f:
                rawdata_grp = f.create_group('raw_data')
                settings_grp = f.create_group('settings')
                axes_grp = f.create_group('axes')
                metadata_grp = f.create_group('metadata')

                # create a group for each instrument
                for inst_name in self.instrument_list:
                    inst_group = settings_grp.create_group(inst_name)
                    inst = getattr(self, inst_name)

                    # create a dataset for each parameter, and assign the current value.
                    for par_name, par_val in inst.parameters.items():
                        try:
                            if self.__verbose: print('getting attribute {} from {}'.format(par_name, inst))
                            dtype = getattr(inst, par_name).type
                            data = getattr(inst, par_name).value
                            inst_group.create_dataset(par_name, shape=(1,), dtype=dtype, data=data)
                        except AttributeError:
                            if self.__verbose: print('attribute not found')

                metadata_grp['date'] = time.asctime()
                metadata_grp['type'] = self.__TYPE

    def load_settings_from_h5(self):
        raise NotImplementedError('cannot load settings yet... working on it!')  # TODO: implement load settings

    @QtCore.pyqtSlot(dict)
    def set_measurement_settings(self, settings_dict):
        """ define the settings specific for the scan.

        Args:
            settings_dict: dictionary containing all the settings required to
                perform a scan.
                Keys must match those defined in self.scan_settings.
        """
        for key in self.measurement_settings:
            assert key in settings_dict, 'missing setting for {}'.format(key)
        self.measurement_settings = settings_dict

    @QtCore.pyqtSlot()
    def on_finished(self, signal):
        if self.__verbose: print('-> finished <- signal recieved')
        self.finished.emit(signal)
        self.can_die = True
        print('finished')

    @QtCore.pyqtSlot()
    def on_newData(self, signal):
        if self.__verbose: print('-> newData <- signal recieved')
        self.newData.emit(signal)

    @QtCore.pyqtSlot(float)
    def on_progressChanged(self, signal):
        if self.__verbose: print('-> progressChanged <- signal recieved')
        self.progressChanged.emit(signal)
        print('current_step: {}'.format(signal))

    @QtCore.pyqtSlot(str)
    def on_stateChanged(self, signal):
        if self.__verbose: print('-> stateChanged <- signal recieved')
        self.stateCanged.emit(signal)


class Worker(QtCore.QObject):
    """ Parent class for all workers.

    This class is to be launched and assigned to a thread.

    settings and instruments:
        these are the worker specific settings and instruments required to
        perform a measurement.

    signals emitted:
        finished (): at end of the scan.
        newData (): emitted at each measurement point.
            together with scan current_step information.
        stateChanged (str): emitted when the state of the worker changes.
            Allowed state values are defined in STATE_VALUES.
    """

    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal()
    progressChanged = QtCore.pyqtSignal(float)
    stateChanged = QtCore.pyqtSignal(str)
    STATE_VALUES = ['loading', 'idle', 'changing parameters', 'running', 'failed', 'complete']
    __verbose = parse_setting('general', 'verbose')

    def __init__(self, file, base_instruments, parameters, **kwargs):  # ,**kwargs):
        """ Initialize worker instance.

        Args:
            file:
            base_instruments(:obj:tuple of :obj:str and :obj:generic.Instrument):
                name and instance of the main instruments required
            parameters (list of :obj:`generic.Parameter): parameters to be
                changed throughout this measurement session.
            disconnect_on_parameter_change (bool): if True, it connects and
                disconnects the required instrument every time a parameter needs
                to be set.
            **kwargs: all kwargs are passed as class attributes.
        """
        super().__init__()

        self.file = file
        for inst in base_instruments:
            setattr(self, inst[0], inst[1])
        self.names = []
        self.units = []
        self.instruments = []  # instruments which controls the parameters
        self.methods = []  # parameters to be changed
        self.values = []  # list of values at which to set the parameters

        for param in parameters:
            self.names.append(param[0])
            self.units.append(param[1])
            self.instruments.append(param[2])
            self.methods.append(param[3])
            self.values.append(param[4])

        for key, val in kwargs.items():
            setattr(self, key, val)

        # Flags
        self.__shouldStop = False  # soft stop, for interrupting at end of cycle.
        self.__state = 'none'
        self.current_index = None  # used to keep track of which parameter to change at each iteration
        self.current_step = 0  # keep track of the current_step of the scan
        self.n_of_steps = 0  # total number of steps of current_step to increment
        self.single_measurement_steps = 1  # number of steps in each measurement procedure

    @QtCore.pyqtSlot()
    def test(self):
        print('test passed')

    @QtCore.pyqtSlot()
    def work(self):
        """ Iterate over all parameters and measure.

        This method iterates over all values of the parameters and performs a
        measurement for each combination. The order defined will be maintained,
        and the effective result is taht of running a nested for loop with the
        first parameter being the outermost loop and the last, the innermost.

        :example:
        with
        parameter_methods = [set_temperature, set_polarization]
        parameter_values = [[10,20,30,40,50],[0,1,2,3]]
        will generate the equivalent of this loop:
        for temperature_values in parameter_values[0]:
            for polarization_values in parameter_values[1]:
                parameter_methods[0](temperature_values)
                parameter_methods[1](polarization_values)
                measure()
        """
        if self.__verbose: print('worker started working')
        ranges = []
        self.__max_ranges = []

        for iter_vals in self.values:
            maxrange = len(iter_vals)
            ranges.append((0, maxrange))
            self.__max_ranges.append(maxrange)
        self.initialize_progress_counter()
        # initialize the indexes control variable
        self.current_index = [-1 for x in range(len(ranges))]

        if self.__verbose: print('starting measurement loop!')
        for indexes in iterate_ranges(ranges):  # iterate over all parameters, and measure
            if self.__shouldStop:
                break
            print(indexes)
            self.set_parameters(indexes)
            self.measure()

        self.finished.emit()
        self.state = 'complete'

    def set_parameters(self, indexes):
        """ change the parameters to the corresponding index set.

        Leaves unchanged the parameter whose index hasn't changed on this iteration.

        Args:
            indexes (:obj:list of :obj:int): list of indexes of the parameter loops
            """
        self.state = 'changing parameters'
        for i, index in enumerate(indexes):
            # if the index corresponding to the parameter i has changed in this
            # iteration, set the new parameter
            print(index, self.current_index)
            if index != self.current_index[i]:
                if self.__verbose: print('setting parameters for iteration {}:'.format(indexes)+
                                         '\nchanging {}.{} to {}'.format(self.instruments[i], self.methods[i],self.values[i][index]))
                # now call the method of the instrument class with the value at#
                #  this iteration
                getattr(self.instruments[i], self.methods[i])(self.values[i][index])
                self.current_index[i]+=1

    def measure(self):
        """ Perform a measurement step.

        This method is called at every iteration of the measurement loop."""
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

    def initialize_progress_counter(self):
        if self.__verbose: print('initializing counter')
        self.n_of_steps = 1
        for i in self.__max_ranges:
            self.n_of_steps *= i
        self.n_of_steps *= self.single_measurement_steps
        if self.__verbose: print('{} loop steps expected'.format(self.n_of_steps))

    def increment_progress_counter(self):
        self.current_step += 1
        self.progress = 100*self.current_step / self.n_of_steps
        self.progressChanged.emit(self.progress)

    @property
    def state(self):
        """ Get the current worker _state:

        Allowed States:
            loading: worker is setting up initial conditions.
            idle: ready to run, awaiting starting condition.
            running: obvious.
            error: worker stuck because of error or something.
        """
        return self.__state

    @state.setter
    def state(self, value):
        """ set new _state flag.

        Sets a new _state, emits a signal with the changed _state value.
        """
        assert value in self.STATE_VALUES, 'invalid status: {}'.format(value)
        self.__state = value
        self.stateChanged.emit(value)

    @QtCore.pyqtSlot(bool)
    def should_stop(self, flag):
        """ Soft stop, for interrupting at the end of the current cycle.

        For hard stop, use kill_worker slot.
        """
        self.__shouldStop = flag

    @QtCore.pyqtSlot()
    def kill_worker(self):
        """ Safely kill the thread by closing connection to all insturments.

        """
        print('killing worker')
        for instrument in self.requiredInstruments:
            try:
                getattr(self, instrument).disconnect()
                print('closed connection to {}'.format(instrument))
            except AttributeError:
                pass
            except Exception as e:
                raise_Qerror('killing {}'.format(instrument), e, popup=False)


if __name__ == "__main__":
    import os

    if os.getcwd()[-9] != 'FemtoScan':
        os.chdir('../')
    main()
