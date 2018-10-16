# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 16:08:39 2018

@author: GVolM

    Copyright (C) 2018 Vladimir Grigorev, Steinn Ymir Agustsson

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
from configparser import ConfigParser


class ExperimentalSetup(object):
    """ WARNING: WORK IN PROGRESS"""

    def __init__(self, **kwargs):
        self.instrument_list = []

        for key, val in kwargs.items():
            self.add_instrument(key, val)

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
        assert isinstance(model, Instrument), '{} is not a recognized instrument type'.format(model)
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
        for inst in self.instrument_list:
            delattr(self, inst)
        self.instrument_list = []


class Instrument(object):
    def __init__(self):
        self.connection_type = 'COM'
        self.configuration = {}
        self.instrument_name = 'Test'

        # self.load_configuration()

    def connect(self):
        raise NotImplementedError('method not implemented for the current model')

    def disconnect(self):
        raise NotImplementedError('method not implemented for the current model')

    def read(self, command):
        raise NotImplementedError('method not implemented for the current model')

    def write(self, command):
        raise NotImplementedError('method not implemented for the current model')

    def version(self):
        """ return the version of the instrument"""
        return 'test Instrument 0.0'

    def save_configuration(self, file):
        raise NotImplementedError('method not implemented for the current model')

    def load_configuration(self, file):
        raise NotImplementedError('method not implemented for the current model')

    def set_configuration(self):
        raise NotImplementedError('method not implemented for the current model')

    def get_configuration(self):
        raise NotImplementedError('method not implemented for the current model')


class parameter(object):
    """ [DEPRECATED] Value which can be set/read from the instrument."""

    def __init__(self, parent_instrument, **kwargs):
        assert isinstance(parent_instrument, Instrument)
        # self.name
        self.parent_instrument = parent_instrument
        self.value = None
        self.value_type = None
        self.codex = {}  # dictionary that converts humanly readable values into the instruments command value


        self.default_value = 0
        self.CONFIRM_VALUE_IS_SET = True

        for key, val in kwargs.items():
            # if the kwarg passed is in the initialized list, assign the value,
            # otherwise ignore it.

            if hasattr(self, key):
                setattr(self, key, val)
            else:
                pass

    def set(self, val):

        # assert type(val) in (str, self.value_type)
        # if type(val) == str:
        #     val = self.codex[val]
        # command = self.write_cmd_head + str(val) + self.write_cmd_tail
        # self.parent_instrument.write(command)
        # if self.CONFIRM_VALUE_IS_SET:
        #     self.get()
        raise NotImplementedError('set function not implemented in this parameter class')

    def get(self):
        # """ Read the value from the instrument"""
        # command = self.read_cmd_head + self.read_cmd_tail
        # readVal = self.parent_instrument.read(self.read_command)
        # self.value = readVal
        # return readVal
        raise NotImplementedError('set function not implemented in this parameter class')



if __name__ == '__main__':
    inst = Instrument()
    inst.configuration['set1'] = '1'
    inst.configuration['set2'] = '2'
    inst.configuration['set3'] = '3'
    print(inst.configuration)

    inst.save_configuration('test')


class NotConnectedError(Exception):
    pass
