# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 20:04:53 2019

@author: vgrigore
"""

import sys, os
import platform
import ctypes
from ctypes import byref, cast, POINTER, c_int, string_at
import time
import platform
import tempfile
import re
import numpy as np
import logging
from utilities.exceptions import DeviceNotFoundError
from instruments.delaystage import DelayStage, StageError

ximc_dir = 'E:/STANDA_TESTS/ximc-2.10.5/ximc/'
ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python")
sys.path.append(ximc_package_dir)
if platform.system() == "Windows":
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"
    libdir = os.path.join(ximc_dir, arch_dir)
    os.environ["Path"] = libdir + ";" + os.environ["Path"]  # add dll

try:
    import pyximc

    lib = pyximc.lib
except ImportError as err:
    print(
        "Can't import pyximc module. The most probable reason is that you changed the relative location of the testpython.py and pyximc.py files. See developers' documentation for details.")
except OSError as err:
    print(
        "Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")


class StandaStage_8SMC5(DelayStage):


    def __init__(self):
        super(StandaStage_8SMC5, self).__init__()
        self.logger = logging.getLogger('{}.Standa_8SMC5'.format(__name__))
        self.logger.info('Created new instance')
        self.step_to_um_factor = 1.25
        self.step_to_ps_factor = 2 * 0.00333564 * self.step_to_um_factor
        self.max_speed = 1000
        self.pos_zero = 0
        self.pos_max = 10000
        self.pos_min = 0
        self._devenum = None
        self.device_number = None
        self.dev_id = None

    def step_to_um(self, pos, uPos):
        return (pos + uPos / 256) * self.step_to_um_factor

    def step_to_ps(self, pos, uPos):
        return (pos + uPos / 256) * self.step_to_ps_factor

    def um_to_step(self, val):
        pos = int(val // self.step_to_um_factor)
        uPos = int((val % self.step_to_um_factor) * 256)
        return pos, uPos

    def ps_to_step(self, val):
        pos = int(val // self.step_to_ps_factor)
        uPos = int((val % self.step_to_ps_factor) * 256)
        return pos, uPos

    def connect(self, device_number=None):
        if device_number is not None:
            self.device_number = device_number
        if self._devenum is None:
            self._devenum = self.get_device_list()

        open_name = lib.get_device_name(self._devenum, self.device_number)
        self.dev_id = lib.open_device(open_name)
        self.logger.debug("Device id: " + repr(self.dev_id))
        result = lib.get_device_information(self.dev_id, byref(pyximc.device_information_t()))
        if result == 0:
            self.logger.debug("Connected to device ID: {}".format(self.dev_id))

    def disconnect(self):
        lib.close_device(byref(cast(self.dev_id, POINTER(c_int))))
        self.logger.debug("Disconnected stage ID: {}".format(self.dev_id))

    def move_absolute(self, new_position, unit='ps'):
        """ move stage to given position, expressed in the defined units ,relative to zero_position"""
        # new_position += self.zero_position # uncomment to use zero position
        if unit == 'ps':
            pos,uPos = self.ps_to_step(new_position)
        elif unit == 'um':
            pos,uPos = self.um_to_step(new_position)
        else:
            raise ValueError('Could not understand {} as unit. please use ps (picoseconds) or um (micrometers)'.format(unit))
        self.logger.debug("Move Absolute dev{} to {} {}".format(self.dev_id,new_position, unit))
        self._move_to(pos,uPos)


    def move_relative(self, distance,unit='ps'):
        """ Evaluate shift in unit of stepper motor steps, and go there."""

        cpos,cuPos = self._get_current_position()
        if unit == 'ps':
            pos, uPos = self.ps_to_step(distance)
        elif unit == 'um':
            pos, uPos = self.um_to_step(distance)
        else:
            raise ValueError('Could not understand {} as unit. please use ps (picoseconds) or um (micrometers)'.format(unit))
        self.logger.debug("Move relative dev{} by {} {}".format(self.dev_id,distance, unit))

        self._move_to(cpos+pos, cuPos+uPos)

    def _move_to(self, pos, uPos=0):
        """ Move stage to the indicated position. In units of steps and microsteps."""
        uPos = uPos % 256
        pos = pos + uPos // 256
        result = lib.command_move(self.dev_id, pos, uPos)
        if result == 0:
            cur_pos, cur_uPos = self._get_current_position()
            d = np.abs(pos - cur_pos)
            ud = np.abs(uPos - cur_uPos)
            wait = (d + ud / 256) / self.speed + .1
            self.logger.debug('Stage{} moved by {}.{}, to {}.{}. Waiting {}s'.format(self.dev_id,d,ud,pos,uPos,wait))
            time.sleep(wait)
        else:
            raise StageError('Standa stage error code {}'.format(result))


    def set_zero_position(self): #TODO: implement zero positioning.
        raise NotImplementedError
        # print('Zero position set to ' + str(self.position_current))
        # self.pos_zero = self.position_current
        # self.position_max = self.position_max - self.position_current
        # self.position_min = self.position_min - self.position_current
        # self.position_current = 0

    def _get_current_position(self):
        x_pos = pyximc.get_position_t()
        result = lib.get_position(self.dev_id, byref(x_pos))
        if self.error_lookup(result):
            pos = x_pos.Position
            uPos = x_pos.uPosition
            self.logger.debug('dev_{} @ position: {}.{} steps'.format(self.dev_id,pos,uPos))
            return pos,uPos

    @property
    def position_um(self):
        pos, upos = self._get_current_position()
        return self.step_to_um(pos, upos)

    @position_um.setter
    def position_um(self, val):
        pos, uPos = self.um_to_step(val)
        self._move_to(pos, uPos)

    @property
    def position_ps(self):
        pos, upos = self._get_current_position()
        return self.step_to_ps(pos, upos)

    @position_ps.setter
    def position_ps(self, val):
        pos, uPos = self.ps_to_step(val)
        self._move_to(pos, uPos)

    @property
    def position_step(self):
        pos, upos = self._get_current_position()
        return pos, upos

    @position_step.setter
    def position_step(self, step,uStep):
        self._move_to(step, uStep)

    @property
    def serial(self):
        x_serial = ctypes.c_uint()
        result = lib.get_serial_number(self.dev_id, byref(x_serial))
        if self.error_lookup(result):
            return (repr(x_serial.value))

    @property
    def speed(self):
        mvst = pyximc.move_settings_t()
        result = lib.get_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            return mvst.Speed

    @speed.setter
    def speed(self, val):
        assert 0 < val < self.max_speed
        mvst = pyximc.move_settings_t()
        result = lib.get_move_settings(self.dev_id, byref(mvst))
        mvst.Speed = int(val)
        result = lib.set_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            print('Speed set to {} step/s'.format(val))

    @property
    def uSpeed(self):
        mvst = pyximc.move_settings_t()
        result = lib.get_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            return mvst.uSpeed

    @uSpeed.setter
    def uSpeed(self, val):
        mvst = pyximc.move_settings_t()
        mvst.uSpeed = int(val)
        result = lib.set_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            print('uSpeed set to {} uStep/s'.format(val))

    @property
    def acceleration(self):
        mvst = pyximc.move_settings_t()
        result = lib.get_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            return mvst.Accel

    @acceleration.setter
    def acceleration(self, val):
        mvst = pyximc.move_settings_t()
        mvst.Accel = int(val)
        result = lib.set_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            print('Acceleration changed to {}'.format(val))

    @property
    def deceleration(self):
        mvst = pyximc.move_settings_t()
        result = lib.get_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            return mvst.Decel

    @deceleration.setter
    def deceleration(self, val):
        mvst = pyximc.move_settings_t()
        mvst.Decel = int(val)
        result = lib.set_move_settings(self.dev_id, byref(mvst))
        if self.error_lookup(result):
            print('Deceleration changed to {}'.format(val))

    def error_lookup(self, id):
        if id == 0:
            return True
        elif id == -1:
            raise Exception('Standa stage error code {}'.format(id))
        elif id == -2:
            raise NotImplementedError('Standa stage error code {}'.format(id))
        elif id == -3:
            raise ValueError('Standa stage error code {}'.format(id))
        elif id == -4:
            raise DeviceNotFoundError('Standa stage error code {}'.format(id))

    @staticmethod
    def get_device_list():
        """ Find all available devices and return the enumeration of them."""
        probe_flags = pyximc.EnumerateFlags.ENUMERATE_PROBE  # + EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr=192.168.0.1,172.16.2.3"
        devenum = lib.enumerate_devices(probe_flags, enum_hints)
        dev_count = lib.get_device_count(devenum)
        print("Device count: " + repr(dev_count))
        controller_name = pyximc.controller_name_t()
        for dev_ind in range(0, dev_count):
            enum_name = lib.get_device_name(devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            if result == pyximc.Result.Ok:
                print("Enumerated device #{} name (port name): ".format(dev_ind) + repr(
                    enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")

        return devenum

    def device_info(self):
        if self.dev_id is not None:
            x_device_information = pyximc.device_information_t()
            result = lib.get_device_information(self.dev_id, byref(x_device_information))
            if self.error_lookup(result):
                print('Device info:')
                print("Device information:")
                print(" Manufacturer: " +
                      repr(string_at(x_device_information.Manufacturer).decode()))
                print(" ManufacturerId: " +
                      repr(string_at(x_device_information.ManufacturerId).decode()))
                print(" ProductDescription: " +
                      repr(string_at(x_device_information.ProductDescription).decode()))
                print(" Major: " + repr(x_device_information.Major))
                print(" Minor: " + repr(x_device_information.Minor))
                print(" Release: " + repr(x_device_information.Release))
        else:
            print('no device selected yet')

    def get_device_status(self):
        if self.dev_id is not None:
            x_status = pyximc.status_t()
            result = lib.get_status(self.dev_id, byref(x_status))
            if self.error_lookup(result):
                fields = [x for x in dir(x_status) if '_' not in x]
                status = {}
                for field in fields:
                    status[field] = repr(getattr(x_status,field))
        else:
            print('no device selected yet')

    def print_device_status(self):
        d = self.get_device_status()
        if d is not None:
            print('Status of device {}'.format(self.dev_id))
            for key,val in d.items():
                print(' - {}: {}'.format(key,val))


if __name__ == "__main__":
    import logging
    from logging.config import fileConfig

    logging.basicConfig(format='%(levelname)s | %(message)s', level=logging.DEBUG)#, filename='example.log')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.debug('Started logger')



    sc = StandaStage_8SMC5()
    sc.connect(0)
    sc.print_device_status()
    print('Current speed settings: {}'.format(sc.speed))
    setspeed = 900
    sc.speed = setspeed
    print('Speed changed to {} speed settings reads: {}\n'.format(setspeed,sc.speed))

    print('\ncurrent pos: {} ps | {} um| {},{} step \n'.format(sc.position_ps,sc.position_um,*sc.position_step))
    moveby = -1#ps
    print('move by {} ps'.format(sc.ps_to_step(moveby)))
    sc.move_relative(moveby,unit='ps')
    print('\ncurrent pos: {} ps | {} um| {},{} step \n'.format(sc.position_ps,sc.position_um,*sc.position_step))
    #
    positions = np.linspace(100,110,1)
    print(positions)
    y = []
    for pos in positions:
        print('going to pos {}'.format(pos))
        sc.move_absolute(pos)
        y.append(sc.position_ps)
    # import matplotlib.pyplot as plt
    # plt.figure()
    # plt.plot(positions,y)
    # plt.show()
    # TODO: try improve precision with accel and decel
    for vv in zip(positions,y,(y-positions)*1000):
        print(*vv,sep='  |  ')
    # print('---- Y ----\n',*y,sep='\n')
    # print(*positions,sep='\n')
    sc.disconnect()
