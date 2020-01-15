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
import sys, os
from instruments.delaystage.generic import DelayStage, StageError
try:
    import thorlabs_apt as apt
except:
    print("no thorlabs_apt found")
sys.path.insert(0, './..')

class ThorLabs_rotational_stage(DelayStage):  # added by Amon sorry if not good
    def __init__(self):
        # super(StandaStage, self).__init__()
        self.serial_N = 27504383

    def connect(self):
        self.serial_N = apt.list_available_devices()[0][1]
        self.motor = apt.Motor(self.serial_N)
        self.motor.disable()
        self.motor.enable()
        # self.motor.move_home()
        while self.motor.is_in_motion:
            time.sleep(1)

    def move_absolute(self, position):
        while self.motor.is_in_motion:
            time.sleep(1)
        self.motor.move_to(position)
        while self.motor.is_in_motion:
            time.sleep(1)

    def disconnect(self):
        pass
        # self.motor.disable()


def main():
    pass


if __name__ == '__main__':
    main()