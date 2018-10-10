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
    def __init__(self):
        self.instrument_list = []

    def add_instrument(self, name, model):
        """ Add an instrument to the experimental setup

        adds as a class attribute an instance of a given model of an instrument,
        with a name of choice.

        This is intended to use by calling ExpSetup.<instrument name>

        : parameters :
            name: str
                name to give to this specific instrument
            model: Instrument
                instance of the class corresponding to the model of this instrument
        """
        assert isinstance(model,Instrument), '{} is not a recognized instrument type'.format(model)
        setattr(self,name,model)
        self.instrument_list.append(name)

    def print_setup(self):
        for name in self.instrument_list:
            print('{}: type:{}'.format(name,type(getattr(self,name))))



class Instrument(object):
    def __init__(self):
        self.connection_type = 'COM'
        self.configuration = {}
        self.instrument_name = 'Test'
        # self.load_configurution()

    def connect(self):
        print('unable to connect to the real instrument, function is not yet implemented')
        pass

    def disconnect(self):
        print('unable to disconnect from the real instrument, function is not yet implemented')
        pass

    def read(self, command):
        print('unable to read from the real instrument, function is not yet implemented')
        pass

    def write(self, command):
        print('unable to write to the real instrument, function is not yet implemented')
        pass

    def save_configurution(self, file):
        cfg = ConfigParser()
        cfg.read_dict(self.configuration)
        with open('{}.ini'.format(file), 'wb') as f:
            print('saving')
            cfg.write(f)


    def load_configurution(self, file):
        pass

    def set_configurution(self):
        pass

    def get_configurution(self):
        pass

if __name__ == '__main__':
    inst = Instrument()
    inst.configuration['set1'] = '1'
    inst.configuration['set2'] = '2'
    inst.configuration['set3'] = '3'
    print(inst.configuration)

    inst.save_configurution('test')