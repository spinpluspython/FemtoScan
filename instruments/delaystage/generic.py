# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson

    Copyright (C) 2018 Steinn Ymir Agustsson

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
from instruments import generic

class DelayStage(generic.Instrument):
    def __init__(self):
        super(DelayStage, self).__init__()
        self.position_zero = 0
        self.position_current = 0
        self.path = 1
        self.position_max = 150
        self.position_min = -150
        self.position_in_ps = 2 * 3.33333 * self.path * self.position_current
        self.configuration = {'zero position': 0}
        self.velocity = 10  # units per second

    def connect(self):
        print('connetcted to fake stage. current position=' + str(self.position_current) + '; zero possition' + str(
            self.position_zero))

    def disconnect(self):
        print('Fake stage has been disconnected')

    def move_absolute(self, new_position):
        # pos=new_position-self.position_zero
        time_to_sleep = (abs(self.position_current - new_position)) / self.velocity
        if (new_position <= self.position_max) and (new_position >= self.position_min):
            'here should be command for real stage; use pos for the real stage'
            self.position_current = new_position
            time.sleep(time_to_sleep)
            print('Fake stage was moved to ' + str(new_position))
        else:
            print('position is out of range')

    def move_relative(self, shift):
        if (self.position_current + shift <= self.position_max) and (
                self.position_current + shift >= self.position_min):
            self.move_absolute(self.position_current + shift)
            print('Fake stage was moved by ' + str(shift))
        else:
            print('position is out of range')

    def set_zero_position(self):
        print('Zero position set to ' + str(self.position_current))
        self.position_zero = self.position_current
        self.position_max = self.position_max - self.position_current
        self.position_min = self.position_min - self.position_current
        self.position_current = 0

    def position_get(self):
        return self.position_current

class StageError(Exception):
    pass

def main():
    pass


if __name__ == '__main__':
    main()