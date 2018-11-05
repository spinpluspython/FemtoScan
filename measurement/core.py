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
from utilities.misc import nested_for, iterate_ranges
from utilities.exceptions import RequirementError
from utilities.math import globalcounter


def main():
    from instruments.lockinamplifier import SR830

    exp = Experiment()
    exp.add_instrument('lockin', SR830())

    print(os.getcwd())
    pass


class Experiment(QtCore.QObject):
    """ Experiment manager class.

    An object of this class is intended to control an experiment.

    This is done by adding to it instruments, via the :obj:add_instrument* method.

    A measurement sesion can be defined by adding parameter iterations.
    This is done by using the method `add_parameter_iteration`, which creates a
    tuple of 3 objects: the *instrument*, the *parameter* and *values*.
    **Instrument**: is an instance of the instrumentwhich will be used to
    control this parameter.
    **parameter** is the name under which this parameter can be found in the
    insutrment object instance
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
            together with scan progress information.
        stateChanged (str): emitted when the state of the worker changes.
            Allowed state values are defined in STATE_VALUES. Bounced from worker.

    """
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

    def add_parameter_iteration(self, instrument, parameter, values):
        """ adds a measurement loop to the measurement plan.

        Args:
            instrument (generic.Instrument): instance of an instrument.
            parameter (str): name of a parameter belonging to instrument, to
                be iterated on.
            values(:obj:list or :obj:tuple): list of parameters to be set, in
                the order in which they will be iterated.
        Raises:
            AssertionError: when any of the types are not respected.
        """
        assert isinstance(instrument, generic.Instrument)
        assert isinstance(parameter, str)
        assert hasattr(instrument, parameter)
        assert isinstance(values, (list, tuple))

        self.measurement_parameters.append((instrument, parameter, values))

    def check_requirements(self):
        """ check if the minimum requirements are fulfilled.
        Raises:
            RequirementError: if any requirement is not fulfilled.

            """
        missing = [x for x in self.required_instruments]

        for instrument in self.instrument_list:

            for i, inst_type in enumerate(self.required_instruments):
                if isinstance(getattr(self, instrument), inst_type):
                    print('found {} as {}'.format(instrument, inst_type))
                    missing.remove(inst_type)
                    break
        if len(missing) > 0:
            raise RequirementError('no instrument of type {} present.'.format(missing))
        elif not os.path.isfile(self.measurement_file):
            raise FileNotFoundError('no File defined for this measurement.')
        else:
            print('all requrements met. Good to go!')

    def get_parameters(self):
        """ Find all parameters which can be set and write them to a dictionary in self.parameters"""
        for instrument in self.instrument_list:
            instrument_instance = getattr(self, instrument)
            for attr, val in instrument_instance.__dict__.items():
                if isinstance(getattr(self.instrument_instance, attr), generic.Parameter):
                    self.parameters[instrument][attr] = getattr(self.instrument_instance, attr)

    def add_instrument(self, name, model):
        """ Add an instrument to the experimental setup

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

    def clear_instrument_list(self):
        """ Remove all instruments from the current instance."""
        self.disconnect_all()
        for inst in self.instrument_list:
            delattr(self, inst)
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
                             self.measurement_parameters,
                             self.measurement_instruments,
                             **self.measurement_settings)

        self.w.finished.connect(self.on_finished)
        self.w.newData.connect(self.on_newData)
        self.w.progressCanged[float].connect(self.on_progressCanged)
        self.w.stateChanged[str].connect(self.on_stageCanged)

        self.w.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.w.work)
        self.scan_thread.start()

    def create_file(self, name=None, dir='D:/Data/', replace=True):
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

        filename = dir + name
        self.measurement_file = filename
        if os.path.isfile(filename) and replace:
            raise NameError('name already exists, please change.')
        else:
            with h5py.File(filename, 'w', libver='latest') as f:
                data_grp = f.create_group('data')
                settings_grp = f.create_group('settings')
                axes_grp = f.create_group('axes')
                metadata_grp = f.create_group('metadata')

                # create a group for each instrument
                for inst_name in self.instrument_list:
                    inst_group = settings_grp.create_group(inst_name)
                    inst = getattr(self, inst_name)

                    # create a dataset for each parameter, and assign the current value.
                    for par_name, par_val in inst.parameters.items():
                        dtype = getattr(par_name, inst_name).type
                        data = getattr(par_name, inst_name).value
                        inst_group.create_dataset(par_name, shape=(1,), dtype=dtype, data=data)
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
        self.finished.emit(signal)

    @QtCore.pyqtSlot()
    def on_newData(self, signal):
        self.newData.emit(signal)

    @QtCore.pyqtSlot(float)
    def on_progressCanged(self, signal):
        self.progressChanged.emit(signal)

    @QtCore.pyqtSlot(str)
    def on_stateCanged(self, signal):
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
            together with scan progress information.
        stateChanged (str): emitted when the state of the worker changes.
            Allowed state values are defined in STATE_VALUES.
    """

    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal()
    progressChanged = QtCore.pyqtSignal(float)
    stateChanged = QtCore.pyqtSignal(str)
    STATE_VALUES = ['loading', 'idle', 'changing parameters', 'running', 'failed', 'complete']

    def __init__(self, file, base_instruments, parameters,
                 disconnect_on_parameter_change=True, **kwargs):
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
            setattr(self, inst)
        self.instruments = []  # instruments which controls the parameters
        self.parameters = []  # parameters to be changed
        self.values = []  # list of values at which to set the parameters

        for param in parameters:
            self.instruments.append(param[0])
            self.parameters.append(param[1])
            self.values.append(param[2])

        for key, val in kwargs.items():
            setattr(self, key, val)

        # Flags
        self.__shouldStop = False  # soft stop, for interrupting at end of cycle.
        self.__state = 'none'
        self.__disconnect_on_paramter_change = disconnect_on_parameter_change
        self.__last_index = None # used to keep track of which parameter to change at each iteration
        self.__progress = 0 # keep track of the progress of the scan
        self.__max_progress = 0 # total number of steps of __progress to increment
        self.__single_measurement_steps = 1 # number of steps in each measurement procedure

    #
    # def check_requirements(self):
    #     """ Check if all required instruments and settings were passed.
    #
    #     """
    #     availableInstruments = []
    #     availableSettings = []
    #     for key, val in self.instruments.items():  # create list of available instruments
    #         availableInstruments.append(key)
    #     for key, val in self.instruments.items():  # create list of available settings
    #         availableSettings.append(key)
    #     for instrument in self.requiredInstruments:  # rise error for each missing instrument
    #         if instrument not in availableInstruments:
    #             raise NotImplementedError('Instrument {} not available.'.format(instrument))
    #     for setting in self.requiredSettings:  # rise error for each missing Setting
    #         if setting not in availableSettings:
    #             raise NotImplementedError('Setting {} not available.'.format(instrument))
    #
    # def initialize_instruments(self):
    #     """ create class attribute for each required instrument and setting.
    #
    #     """
    #     for inst in self.requiredInstruments:
    #         try:
    #             # inst_string = str(instrument).lower().replace('-', '')
    #             setattr(self, inst, self.instruments[inst])
    #         except KeyError:
    #             raise KeyError('Instrument {} not available.'.format(inst))
    #     for setting in self.requiredSettings:
    #         try:
    #             setattr(self, setting, self.settings[setting])
    #         except KeyError:
    #             raise KeyError('Setting {} not available.'.format(setting))

    def measurement_loop(self):
        """ Iterate over all parameters and measure.

        This method iterates over all values of the parameters and performs a
        measurement for each combinaion. The order defined will be maintained,
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

        ranges = []
        self.__max_ranges = []

        for iter_vals in self.values:
            maxrange = len(iter_vals)
            ranges.append((0, maxrange))
            self.__max_ranges.append(maxrange)
        self.initialize_progress_counter()
        # initialize the indexes control variable
        self.__last_index = [0 for x in range(len(ranges))]

        for indexes in iterate_ranges(ranges):  # iterate over all parameters, and measure
            if self.__shouldStop:
                break
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
        self.state = 'Changing Parameters'
        for i, index in enumerate(indexes):
            # if the index corresponding to the parameter i has changed in this
            # iteration, set the new parameter
            if index != self.__last_index[i]:
                if self.__disconnect_on_paramter_change:
                    self.instruments[i].connect()
                # as this should be a generic.Parameter class object, it should
                # have a set method, to change its value.
                getattr(self.instruments[i], self.parameters[i]).set(self.values[i][index])
                if self.__disconnect_on_paramter_change:
                    self.instruments[i].disconnect()

    def work(self):
        """ main loop, worker specific."""
        # TODO: add assertions to make sure scan CAN start
        print('starting a measurement loop')  # TODO: add mode description to print
        self.measurement_loop()

    def measure(self):
        """ Perform a measurement step.

        This method is called at every iteration of the measurement loop."""
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

    def initialize_progress_counter(self):
        self.__max_progress = 1
        for i in self.__max_ranges:
            self.__max_progress *= i
        self.__max_progress *= self.__single_measurement_steps

    def increment_progress_counter(self):
        self.__progress += 1
        self.progressChanged.emit(self.__progress / self.__max_progress)

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
