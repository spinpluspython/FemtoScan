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
import time
import sys, os
from .generic import DelayStage
try:
    import clr
    import System
except ImportError:
    print('missing packages for Newport stage.')

class NewportXPS(DelayStage):

    def __init__(self):
        super(NewportXPS, self).__init__()
        if 'CommandInterfaceXPS' not in sys.modules:  # TODO: fix imports for XPS stage
            # TODO: implement test and ask for correct path in case of faliure
            self.NETAssemblyPath = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_1.0.0.0__9a267756cf640dcf'
            sys.path.append(self.NETAssemblyPath)
            clr.AddReference("Newport.XPS.CommandInterface")
            import CommandInterfaceXPS

        self.myXPS = CommandInterfaceXPS.XPS()
        self.Address = '192.168.254.254'
        self.Port = 5001
        self.StageName = "CykBlyat"
        self.velocity = 500
        self.position_zero = -100
        self.position_current = 0
        self.position_max = 150
        self.position_min = -150

    def XPS_Open(self):
        # Create XPS interface
        # Open a socket
        timeout = 1000
        result = self.myXPS.OpenInstrument(self.Address, self.Port, timeout)
        if result == 0:
            print('Open ', self.Address, ":", self.Port, " => Successful")
        else:
            print('Open ', self.Address, ":", self.Port, " => failure ", result)

    def connect(self):
        self.XPS_Open()
        self.myXPS.GroupKill(System.String(self.StageName), System.String(""))
        self.myXPS.GroupInitialize(System.String(self.StageName), System.String(""))
        time.sleep(1)
        self.myXPS.GroupHomeSearch(System.String(self.StageName), System.String(""))
        self.myXPS.GroupMotionEnable(System.String(self.StageName), System.String(""))
        self.move_absolute(self.position_zero)

    def move_absolute(self, new_position):
        '''Moves stage to the given position in range of +/- 150 mm '''

        time_to_sleep = (abs(self.position_current - new_position)) / self.velocity
        if (new_position < self.position_max) and (new_position > self.position_min):
            self.myXPS.GroupMoveAbsolute(System.String(self.StageName), [System.Double(new_position)], System.Int32(1),
                                         System.String(""))
            self.position_current = new_position
            time.sleep(time_to_sleep)
            print('DelayStage was moved to ' + str(new_position))
        else:
            print('position is out of range')

    def position_get(self):
        pos = self.myXPS.GetCurrentPosition(System.Double(0), System.Double(0), System.Int32(1), System.Int32(1),
                                            System.Int32(1), System.Int32(1), System.String(self.StageName))
        return pos

    def disconnect(self):
        self.myXPS.GroupKill(System.String(self.StageName), System.String(""))
        print('DelayStage has been disconnected')

    def XPS_GetControllerVersion(self, myXPS, flag):
        result, version, errString = self.myXPS.FirmwareVersionGet(System.String(""), System.String(""))
        if flag == 1:
            if result == 0:
                print('XPS firmware version => ', version)
            else:
                print('FirmwareVersionGet Error => ', errString)
            return result, version

    def XPS_GetControllerState(self, myXPS, flag):
        result, state, errString = self.myXPS.ControllerStatusGet(System.Int32(0), System.String(""))
        if flag == 1:
            if result == 0:
                print('XPS controller state => ', state)
            else:
                print('ControllerStatusGet Error => ', errString)
        return result, state


def main():
    pass


if __name__ == '__main__':
    main()