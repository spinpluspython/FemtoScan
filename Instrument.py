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


class Instrument(object):
    def __init__(self):
        self.connection_type = 'COM'
        self.configuration = {}
        self.load_configurution()

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

    def save_configurution(self):
        pass

    def load_configurution(self):
        pass

    def set_configurution(self):
        pass

    def get_configurution(self):
        pass
