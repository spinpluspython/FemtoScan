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
import logging
from configparser import ConfigParser
import sys
sys.path.insert(0,'./..')

from utilities.exceptions import DeviceNotFoundError, DeviceNotConnectedError


class Instrument(object):

    def __init__(self):
        self.logger = logging.getLogger('{}.Instrument'.format(__name__))
        self.logger.info('Created instance of Generic instrument.')

        self.name = 'Generic Instrument'
        self.measurables = []
        # define properties
        self._settings = {}
        self._connected = False
        self._version = 'Generic Instrument 0.1'

    @property
    def connected(self):
        self.logger.debug("Someone asked if I'm connected... yes! I am")
        return self._connected

    def get_setting(self,setting, key='value'):
        """allowes to read values locally, without promting the device itself."""
        assert isinstance(self,setting), '{} is not an available setting in {}'.format(setting,self.name)
        return self._settings[setting][key]

    def connect(self):
        print('Connecting generic instrument')
        self._connected = True

    def disconnect(self):
        self.logger.info('disconnecting generic instrument')

        self._connected = False

    def read(self, command):
        raise NotImplementedError('method not implemented for the current model')

    def write(self, command):
        raise NotImplementedError('method not implemented for the current model')

    def test_connection(self):
        try:
            self.connect()
            self.version()
        except:
            raise DeviceNotFoundError

    @property
    def version(self):
        return self._version

    @property
    def settings(self):
        """ get the value of all parameters in current state.

        :returns:
            configDict: dict
                dictionary with as keys the parameter name and as values the
                value in the current configuration.
        """
        return self._settings

    @settings.setter
    def settings(self, settingsDict):
        """ get the value of all parameters in current state.

        :parameter:
            settingsDict: dict
                dictionary containing keys for each setting to be changed.
                Values should also be dicts, containing heys for what needs to
                be changed in the settings.
        """
        assert isinstance(settingsDict, dict), 'Settings is supposed to be a dict, not {}'.format(type(settingsDict))
        for key, value in settingsDict.items():
            if isinstance(value, dict):
                for s_key, s_val in value.items():
                    oldval = self._settings[key][s_key]
                    assert type(oldval) == type(s_val), 'wrong type for {}: {}: {}'.format(key, s_key, s_val)
                    if oldval != s_val:
                        print('{} {} changed from {} to {}'.format(key, s_key, oldval, s_val))
                    self._settings[key][s_key] = s_val
            else:
                oldval = self._settings[key]['value']
                assert type(oldval) == type(value), 'wrong type for {}: {}: {}'.format(key, 'value', s_val)
                if oldval != value:
                    print('{} {} changed from {} to {}'.format(key, 'value', oldval, value))
                self._settings[key]['value'] = value

    def save_settings(self, file):  # TODO: rewrite this for new settings structure
        """ Save the current configuration to ini file.

        :parameters:
            file: str
                file name complete with absolute path
        """
        configDict = self.get_settings()
        config = ConfigParser()

        config.add_section(self.name)
        for key, val in configDict.items():
            config.set(self.name, key, str(val))
        if file[-4:] != '.ini':
            file += '.ini'
        with open(file, 'w') as configfile:  # save
            config.write(configfile)

    def load_settings(self, file):  # TODO: rewrite this for new settings structure
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

    inst.save_settings('test')
