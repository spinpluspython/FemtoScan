# -*- coding: utf-8 -*-
"""
Created on Nov 22 09:57:29 2017

@author: S.Y. Agustsson
"""

import time
from PyQt5 import QtCore
from utilities.qt import raise_Qerror

class Experiment(QtCore.QObject):

    def __init__(self):
        super(Experiment, self).__init__()

        self.instruments =1

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

    # def set_status(self,statusString):
    #
    #     self.statusFlag = statusString
    #     self.status.emit(statusString)
    #
    # def get_status(self):
    #     self.status.emit(self.statusFlag)
    #     return self.stautsFlag

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
