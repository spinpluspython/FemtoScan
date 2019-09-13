# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 16:22:35 2018

@author: Vladimir Grigorev, Steinn Ymir Agustsson

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
import time
import sys
try:
    import thorlabs_apt as apt
except:
    print("no thorlabs_apt found")
sys.path.insert(0,'./..')

from instruments import generic 
#import _PyUSMC as _PyUSMC

try:
    import clr
    import System
except ImportError:
    print('missing packages for Newport stage.')


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

#%%
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
#%%standa stage
    
class StandaStage(DelayStage):
    def __init__(self):
        super(StandaStage, self).__init__()
        self.standa=_PyUSMC.StepperMotorController()
        self.stage_N=0
        self.mm_in_step=0.000325 #depend on your stage typ: 0.000125 for standa 055709; 0.000325 for standa 026424
        
    def connect(self):
        self.standa.Init()
        print(str(len(self.standa.motors))+' stages were connected. Change self.stage_N to switch between stages')
        self.motor=self.standa.motors[self.stage_N]
        
        self.motor.position.maxSpeed = 500.0
        
        # Set controller parameters
        self.motor.parameters.Set(
            MaxTemp = 70.0,
            AccelT = 200.0,
            DecelT = 200.0,
            BTimeout1 = 0.0,
            BTimeout2 = 1000.0,
            BTimeout3 = 1000.0,
            BTimeout4 = 1000.0,
            BTO1P = 10.0,
            BTO2P = 100.0,
            BTO3P = 400.0,
            BTO4P = 800.0,
            MinP = 500.0,
            BTimeoutR = 500.0,
            LoftPeriod = 500.0,
            RTDelta = 200,
            RTMinError = 15,
            EncMult = 2.5,
            MaxLoft = 32,
            PTimeout = 100.0,
            SynOUTP = 1)

        # Set start parameters
        self.motor.startParameters.Set(
            SDivisor = 8,
            DefDir = False,
            LoftEn = False,
            SlStart = False,
            WSyncIN = False,
            SyncOUTR = False,
            ForceLoft = False)
        
        # Power on
        self.motor.mode.PowerOn()
        
    def move_absolute(self, new_position):
        self.motor.Start(int(new_position/self.mm_in_step))
        self.position_current = new_position
    
    def position_get(self):
        '''returns current position in mm (accurding to the mm in step parametr)'''
        self.position_current =self.motor.GetPos()*self.mm_in_step
        print(self.motor.GetPos()*self.mm_in_step)
        return self.motor.GetPos()*self.mm_in_step
    
    def disconnect(self):
        self.standa.StopMotors(True)
        self.standa.Close()
        
        
        
        
class ThorLabs_rotational_stage(DelayStage):  #added by Amon sorry if not good
    def __init__(self):
        #super(StandaStage, self).__init__()
        self.serial_N=27504383
        
    def connect(self):
        self.serial_N=apt.list_available_devices()[0][1]
        self.motor=apt.Motor(self.serial_N)
        self.motor.disable()
        self.motor.enable()
        #self.motor.move_home()
        while self.motor.is_in_motion:
            time.sleep(1)
    def move_absolute(self,position):
        while self.motor.is_in_motion:
            time.sleep(1)
        self.motor.move_to(position)
        while self.motor.is_in_motion:
            time.sleep(1)
    def disconnect(self):
        pass
        #self.motor.disable()