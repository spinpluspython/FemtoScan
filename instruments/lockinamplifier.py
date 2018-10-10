# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 17:11:24 2018

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
import Instrument
import random
import time


class Lockin(Instrument.Instrument):
    def __init__(self):
        super(Lockin, self).__init__()

        self.configuration = {'Sensitivity': 0, 'Time constant': 0, 'Reference source': 0,
                              'Frequency': 1, 'Reference trigger': 0}

    def connect(self):
        print('Fake Lockin amplifier is connected')

    def disconnect(self):
        print('Fake Lockin amplifier is disconnected')

    def read_value(self, parameter):
        '''Reads measured value from lockin. Parametr is a string like in manual. 
        except Theta. Che the dictionary of parametrs for Output
        '''
        Value = random.random()  # returns value as a float
        print(parameter + ' = ' + str(Value) + ' V')
        time.sleep(0.1)
        return Value

    # %% set parameters

    def set_sensitivity(self, sens):
        self.configuration['Sensetivity'] = sens

    def set_time_constant(self, const):
        self.configuration['Time constant'] = const

    def set_frequency(self, freq):
        self.configuration['Frequency'] = freq

    def set_reference_source(self, ref):
        self.configuration['Reference source'] = ref

    def set_reference_trigger(self, reftrig):
        self.configuration['Reference trigger'] = reftrig

    # %% get parameters

    def get_sensitivity(self):
        pass

    def get_time_constant(self):
        pass

    def get_frequency(self):
        pass

    def get_reference_source(self):
        pass

    def get_reference_trigger(self):
        pass

    # %% Configuration of lockin functions

    def get_configuration(self):
        self.get_sensitivity()
        self.get_time_constant()
        self.get_frequency()
        self.get_reference_source()
        self.get_reference_trigger()

    def set_configuration(self):
        self.set_sensitivity(self.configuration['Sensitivity'])
        self.set_time_constant(self.configuration['Time constant'])
        self.set_frequency(self.configuration['Frequency'])
        self.set_reference_source(self.configuration['Reference source'])
        self.set_reference_trigger(self.configuration['Reference trigger'])

    def save_configurution(self):
        pass

    def laod_configuration(self):
        pass
