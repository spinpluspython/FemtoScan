# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 16:08:39 2018

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
from configparser import ConfigParser


class Instrument(object):

    def __init__(self):

        self.measurables = [None]
        self.parameters = {}
        self.name = 'Generic Instrument'

        #self.connection_type = None
        #self.configuration = {}
        #self.instrument_model_name = 'Dummy'

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

    def init_parameters(self):
        self.parameters = {}
        for attr, val in self.__dict__.items():
            if isinstance(getattr(self, attr), Parameter):
                # TODO: implement value initialization to read value from device, or default.
                self.parameters[attr] = val

    def get_measurables(self):
        """ Function should return the methods which can be used to record some data."""
        raise NotImplementedError('method not implemented for the current model')

    def get_configuration(self):
        """ get the value of all parameters in current state.

        :returns:
            configDict: dict
                dictionary with as keys the parameter name and as values the
                value in the current configuration.
        """
        configDict = {}
        for item, value in self.parameters.items():
            configDict[item] = value.value
        return configDict

    def set_configuration(self, configDict):
        """ get the value of all parameters in current state.

        :parameter:
            configDict: dict
                dictionary with as keys the parameter name and as values the
                value in the current configuration.
        """
        for key, val in configDict.items():
            assert isinstance(val, Parameter)
            oldval = self.parameters[key].value
            if oldval != val:
                print('{} changed from {} to {}'.format(key, oldval, val))
                self.parameters[key].value = val

    def save_configuration(self, file):
        """ Save the current configuration to ini file.

        :parameters:
            file: str
                file name complete with absolute path
        """
        configDict = self.get_configuration()
        config = ConfigParser()

        config.add_section(self.name)
        for key, val in configDict.items():
            config.set(self.name, key, str(val))
        if file[-4:] != '.ini':
            file += '.ini'
        with open(file, 'w') as configfile:  # save
            config.write(configfile)

    def load_configuration(self, file):  # TODO: fix this, its broken!!
        """ Load a configuration from a previously saved ini file.

        :parameters:
            file: str
                file name complete with absolute path
        """

        config = ConfigParser()
        config.read(file)
        for name in config[self.name]:
            try:
                val = getattr(self, name).type(config[self.name][name])
                getattr(self, name).value = val
            except AttributeError:
                print('no parameter called {} in this device')

    # %% the danger zone:
    def __del__(self):
        """ Disconnect device before loosing it's instance."""
        self.disconnect()


class Parameter(object):
    """ Value which can be set/read from the instrument."""

    def __init__(self, parent_instrument, **kwargs):
        assert isinstance(parent_instrument, Instrument)
        # self.name
        self.parent_instrument = parent_instrument
        self.value = None
        self.value_type = None
        self.codex = {}  # dictionary that converts humanly readable values into the instruments command value
        self.cmd = None

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
        raise NotImplementedError('set function not implemented in this Parameter class')

    def get(self):
        # """ Read the value from the instrument"""
        # command = self.read_cmd_head + self.read_cmd_tail
        # readVal = self.parent_instrument.read(self.read_command)
        # self.value = readVal
        # return readVal
        raise NotImplementedError('set function not implemented in this Parameter class')


if __name__ == '__main__':
    inst = Instrument()
    inst.configuration['set1'] = '1'
    inst.configuration['set2'] = '2'
    inst.configuration['set3'] = '3'
    print(inst.configuration)

    inst.save_configuration('test')
