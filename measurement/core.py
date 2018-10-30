# -*- coding: utf-8 -*-
"""
Created on Nov 22 09:57:29 2017

@author: S.Y. Agustsson
"""
import os, sys
import time
from PyQt5 import QtCore
import h5py


from instruments import generic
from utilities.qt import raise_Qerror
from utilities.misc import nested_for, iterate_ranges
from utilities.math import globalcounter


import pandas as pd


class Experiment(QtCore.QObject):
    __TYPE = 'generic'
    def __init__(self, file=None, **kwargs):
        """ create an instance of the Experiment

        This is initialized by creating adding all the passed arguments as instrument instances, and creates a
        list of names of them in self.instrument_list. Then, all methods which can be used to measure some quantity
        and all parameters which can be set for each instruments are collected in self.measurable_methods and self.parameters
        respectively.

        self.measurable_methods is therefore a list of methods which can be directly called. These methods must have a test on
        the parent instrument being connected, or might fail.
        self. parameters is a dictionary, where keys are the names of the instruments to which they belong. Each value
        is then a dictionary containing the name of the parameter as keys and a pointer to the parameter instance in the
        value.

        :parameters:
            kwargs: generic.Instrument
                The names ofn given keyword arguments will be the specific name of the insturment (example: probe_stage)
                and the value must be an instance of the specific instrument (example: delaystage.NewportXPS)

        """
        super().__init__()

        self.instrument_list = []
        self.measurables = []
        self.measurables_arguments = []

        #TODO: make measurables and parameter setters look something like this:
        self.measurables_TEST = {'readvalue':{'instrument':self.lockinamplifier,
                                              'method':'read_value',
                                              'args':'X',}}

        self.parameters = {}
        self.measurement_file = file
        self.measurement_name = 'unknown measurement '+ time.asctime().replace(':','-')

        if self.measurement_file is not None:
            self.load_settings_from_h5()

        for key, val in kwargs.items():
            self.add_instrument(key, val)

        # self.get_measurables()
        self.get_parameters()

    def get_measurables(self):
        """ Find all measurable methods defined in the list of instruments."""
        measurables_dict = {}
        for inst in self.instrument_list:
            inst_instance = getattr(self, inst)
            measurables = inst_instance.get_measurables()
            measurables_dict[inst] = measurables
        return measurables_dict

    def get_parameters(self):
        """ Find all parameters which can be set and write them to a dictionary in self.parameters"""
        for inst in self.instrument_list:
            inst_instance = getattr(self, inst)
            for attr, val in inst_instance.__dict__.items():
                if isinstance(getattr(self, attr), generic.Parameter):
                    self.parameters[inst][attr] = getattr(self, attr)

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
        """ Experiment type specific method."""
        raise NotImplementedError('no initialization method in this experiment (sub)class')

    def measure(self, measurables, parameter_methods, values):
        """ [deprecated] perform a measurement."""
        raise NotImplementedError('no measure method in this experiment (sub)class')

    def create_file(self,name=None,dir='D:/Data/', replace=True):
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

        filename = dir+name
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
                    inst = getattr(self,inst_name)

                    # create a dataset for each parameter, and assign the current value.
                    for par_name,par_val in inst.parameters.items():
                        dtype = getattr(par_name,inst_name).type
                        data = getattr(par_name,inst_name).value
                        inst_group.create_dataset(par_name,shape=(1,),dtype=dtype,data=data)
                metadata_grp['date'] = time.asctime()
                metadata_grp['type'] = self.__TYPE

    def load_settings_from_h5(self):
        raise NotImplementedError('cannot load settings yet... working on it!')


class StepScan(Experiment):
    __TYPE = 'stepscan'

    def __init__(self):
        super().__init__()

    def initialize_experiment(self):
        """ set up all what is needed for a measurement session.

        - check if measurable methods were chosen.
        - check if parameter iteration methods, and relative values are present
        - check if the file name chosen is already present, otherwise append number
        - write file structure in the h5 file chosen
        - preallocate data file structures
        - disconnect all devices
        """
        assert len(self.measurables) >0, 'need to assign at least one measurement method.'
        assert len(self.measurables_arguments) == len(self.measurables), 'not al measurables have parameters!'





class Worker_methodsbased(QtCore.QObject):
    """ [deprecated] This class manages a measurement session.

    An instance of this class is designed to be sent to a new thread, which will
    output signals to enable control from the original thread (GUI or not).

    Signals:
        newData (list): emitted at each new data aquisition, by the method measure()
            Emitted data is a list containing the results from each measurable method used.
        finished: emitted when the whole measurement procedure is complete.
        cycleEnd : emitted at each end of a measurement cycle

    """
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(list)
    newCycle = QtCore.pyqtSignal(int)
    STATE_VALUES = ['loading', 'idle', 'running', 'error']

    def __init__(self, file, measurable_methods, measurable_values, parameter_methods, parameter_values):
        """ Initialize with measurement and parameter setting methods and values.

        Args:
            file (str): path to file where to save data
            measurable_methods (:obj:`list` of :obj:`method`): functions to run to
                gather data at each measurement step
            measurable_values (:obj:`list` of :obj:`list` of :obj:`float`): values to be
                passed to the measurable methods.
            parameter_methods (:obj:`list` of :obj:`method`): methods to be called
                to change parameters
            parameter_values (:obj:`list` of :obj:`list` of :obj:`float`): values to be
                passed to the parameter setting methods.
        """
        super().__init__()
        self.save_file = file
        self.measurable_methods = measurable_methods
        self.measurable_values = measurable_values
        self.parameter_methods = parameter_methods
        self.parameter_values = parameter_values

        self.__prev_index = None

    def work(self):
        """ Create a loop for each parameter this worker should iterate on.

        The loop will be equivalent to a nested series of for loops, one for
        each list of values in self.parameter_values. The first method will be
        the innermost cycle.

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

        def measurement_step(indexes, parameter_methods, values):
            """ set the correct parameters and start a measurement step"""
            self.newCycle.emit(globalcounter(indexes, self.__max_ranges))  # emit signal with global counter number
            if self.__prev_index is None:  # at first iteration, start keeping track of indexes
                self.__prev_index = []
                for i in range(len(indexes)):
                    self.__prev_index.append(0)

            for i, idx in enumerate(indexes):  # check which parameters need to be changed at this iteration
                if idx != self.__prev_index[i]:
                    parameter_methods[i](values[indexes[i]])  # set only the parameters which change at this cycle

            for i, func in enumerate(parameter_methods):
                func(values[i][indexes[i]])  # set all parameters

            self.measure()

        ranges = []
        self.__max_ranges = []

        for iter_vals in self.parameter_values:
            maxrange = len(iter_vals)
            ranges.append((0, maxrange))
            self.__max_ranges.append(maxrange)

        ranges = tuple(ranges)

        nested_for(ranges, measurement_step, self.parameter_methods, self.parameter_values)
        self.finished.emit()

    def measure(self):
        """ Perform a single point measurement.

        This uses all methods defined in self.measurable_methods to record all data desired.

        """
        result = []
        for i, mtd in enumerate(self.measurable_methods):
            result.append(mtd(self.measurable_values[i]))
        self.newData.emit(result)

    @QtCore.pyqtSlot()
    def kill_worker(self):
        """ Safely kill the thread by closing connection to all insturments."""
        for instrument in self.requiredInstruments:
            try:
                getattr(self, instrument).close()
                print('closed connection to {}'.format(instrument))
            except AttributeError:
                pass
            except Exception as e:
                raise_Qerror('killing {}'.format(instrument), e, popup=False)

    @property
    def state(self):
        """ Get the current worker _state.

        Allowed States:
            loading: worker is setting up initial conditions.
            idle: ready to run, awaiting starting condition.
            running: obvious.
            error: worker stuck because of error or something.
        """
        return self.state

    @state.setter
    def state(self, value):
        """ set new _state flag.

        Sets a new _state, emits a signal with the changed _state value.
        """
        assert value in self.STATE_VALUES, 'invalid status: {}'.format(value)
        self.__state = value
        self.valueChanged.emit(value)

    @QtCore.pyqtSlot(bool)
    def should_stop(self, flag):
        """ Soft stop, for interrupting at the end of the current cycle.

        For hard stop, use kill_worker slot.
        Args:
            flag (bool): True sets the worker to stop after current cycle.
                False turns this option off.
        """
        self.shouldStop = flag


class Worker(QtCore.QObject):
    """ Parent class for all workers.

    This class is to be launched and assigned to a thread.

    settings and instruments:
        these are the worker specific settings and instruments required to
        perform a measurement.

    signals emitted:
        finished (dict): at end of the scan, emits the results stored over the whole scan.
        newData (dict): emitted at each measurement point. Usually contains a dictionary with the last measured values
            together with scan progress information.
        _state (str): emitted when _state of the worker changes. Allowed values of _state are defined in STATE_VALUES.
    """

    finished = QtCore.pyqtSignal(dict)
    newData = QtCore.pyqtSignal(dict)
    progress = QtCore.pyqtSignal(float) # TODO: implement
    STATE_VALUES = ['loading', 'idle', 'running', 'error']

    def __init__(self, file, instruments, parameters):
        super().__init__()

        self._parameters = parameters
        self._instruments = instruments

        self._file = file

        self.result = {'data': []}
        self.result = {**self.result, **self.settings}

        # Flags
        self.__shouldStop = False  # soft stop, for interrupting at end of cycle.
        self.__state = 'none'

        #self.requiredInstruments = []  # fill list with names of instruments required for (sub)class
        #self.requiredSettings = []  # fill list with names of settings required for (sub)class

    def check_requirements(self):
        """ Check if all required instruments and settings were passed.

        """
        availableInstruments = []
        availableSettings = []
        for key, val in self.instruments.items():  # create list of available instruments
            availableInstruments.append(key)
        for key, val in self.instruments.items():  # create list of available settings
            availableSettings.append(key)
        for instrument in self.requiredInstruments:  # rise error for each missing instrument
            if instrument not in availableInstruments:
                raise NotImplementedError('Instrument {} not available.'.format(instrument))
        for setting in self.requiredSettings:  # rise error for each missing Setting
            if setting not in availableSettings:
                raise NotImplementedError('Setting {} not available.'.format(instrument))

    def initialize_instruments(self):
        """ create class attribute for each required instrument and setting.

        """
        for inst in self.requiredInstruments:
            try:
                # inst_string = str(instrument).lower().replace('-', '')
                setattr(self, inst, self.instruments[inst])
            except KeyError:
                raise KeyError('Instrument {} not available.'.format(inst))
        for setting in self.requiredSettings:
            try:
                setattr(self, setting, self.settings[setting])
            except KeyError:
                raise KeyError('Setting {} not available.'.format(setting))

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

        for iter_vals in self.parameter_values:
            maxrange = len(iter_vals)
            ranges.append((0, maxrange))
            self.__max_ranges.append(maxrange)

        # initialize the indexes control variable
        self.__current_index = [0 for x in range(len(ranges))]

        for indexes in iterate_ranges(ranges): #iterate over all parameters, and measure
            if self.__shouldStop:
                break
            self.set_parameters(indexes)
            self.measure()

    def set_parameters(self, indexes):
        """ change the parameters to the corresponding index set.

        Leaves unchanged the parameter whose index hasn't changed on this iteration.

        Args:
            indexes (:obj:list of :obj:int): list of indexes of the parameter loops
            """
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

    def measure(self):
        """ Perform a measurement step.

        This method is called at every iteration of the measurement loop."""
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

    def work(self):
        """ main loop, worker specific."""
        self.measurement_loop()
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

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
        self.valueChanged.emit(value)

    @QtCore.pyqtSlot(bool)
    def should_stop(self, flag):
        """ Soft stop, for interrupting at the end of the current cycle.

        For hard stop, use kill_worker slot.
        """
        self.__shouldStop = flag


def main():
    # w = Worker()
    # w.work()
    pass


if __name__ == "__main__":
    main()
