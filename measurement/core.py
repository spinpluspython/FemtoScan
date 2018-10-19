# -*- coding: utf-8 -*-
"""
Created on Nov 22 09:57:29 2017

@author: S.Y. Agustsson
"""
from instruments import generic
import time
from PyQt5 import QtCore
from utilities.qt import raise_Qerror
from utilities.misc import nested_for

class Experiment(QtCore.QObject):

    def __init__(self, **kwargs):
        """ create an instance of the Experiment

        This is initialized by creating adding all the passed arguments as instrument instances, and creates a
        list of names of them in self.instrument_list. Then, all methods which can be used to measure some quantity
        and all parameters which can be set for each instruments are collected in self.measurables and self.parameters
        respectively.

        self.measurables is therefore a list of methods which can be directly called. These methods must have a test on
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
        self.parameters = {}

        for key, val in kwargs.items():
            self.add_instrument(key, val)

        self.get_measurables()
        self.get_parameters()

    def get_measurables(self):
        """ Find all measurable methods defined in the list of instruments."""
        for inst in self.instrument_list:
            inst_instance = getattr(self, inst)
            measurables = inst_instance.get_measurables()
            for method in measurables:
                self.measurables.append(inst_instance.method)

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

    def measure(self, measurables, parameter_methods, values):
        """ perform a measurement.

        this is a demon.. I hope it works!

        :parameters:
            measurables:
                measuring methods to be performed at each iteration

            parameters: list of methods
                list of methods to use to change the parameters at each iteration.
                example: (stage.move_to,cryostat.set_temperature)
            values: list or tuple of lists or tuples
                the values over which to iterate the parameters.
                example: ([1,2,3,4,5,6,7,8,9,10],[4,8,12,20,30,50,100,200,300])
        """
        def measurement_step(indexes, parameter_methods, values):
            """ set the correct parameters and start a measurement step"""
            result = []
            for i,func in enumerate(parameter_methods):
                func(values[i][indexes[i]]) # set all parameters

            for func in measurables:
                result.append(func())# todo: replace with actual measurement routine (worker)
            return result

        ranges=[]
        for iter_vals in values:
            ranges.append((0,len(iter_vals)))
        ranges = tuple(ranges)

        nested_for(ranges,measurement_step,parameter_methods, values)


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
        state (str): emitted when state of the worker changes. Allowed values of state are defined in STATE_VALUES.
    """

    finished = QtCore.pyqtSignal(dict)
    newData = QtCore.pyqtSignal(dict)
    STATE_VALUES = ['loading', 'idle', 'running', 'error']

    def __init__(self, settings, instruments):
        super(Worker, self).__init__()
        self.settings = settings
        self.instruments = instruments

        self.result = {'data': []}
        self.result = {**self.result, **self.settings}

        # Flags
        self.shouldStop = False  # soft stop, for interrupting at end of cycle.
        self.state = 'none'

        self.requiredInstruments = []  # fill list with names of instruments required for (sub)class
        self.requiredSettings = []  # fill list with names of settings required for (sub)class

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

    def work(self):
        """ main loop, worker specific."""
        raise NotImplementedError("Method 'work' not implemented in worker (sub)class")

    @QtCore.pyqtSlot()
    def kill_worker(self):
        """ Safely kill the thread by closing connection to all insturments.

        """
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
        """ Get the current worker state:

        Allowed States:
            loading: worker is setting up initial conditions.
            idle: ready to run, awaiting starting condition.
            running: obvious.
            error: worker stuck because of error or something.
        """
        return self.state

    @state.setter
    def state(self, value):
        """ set new state flag.

        Sets a new state, emits a signal with the changed state value.
        """
        assert value in self.STATE_VALUES, 'invalid status: {}'.format(value)
        self.state = value
        self.valueChanged.emit(value)

    @QtCore.pyqtSlot(bool)
    def should_stop(self, flag):
        """ Soft stop, for interrupting at the end of the current cycle.

        For hard stop, use kill_worker slot.
        """
        self.shouldStop = flag


def main():
    # w = Worker()
    # w.work()
    pass


if __name__ == "__main__":
    main()
