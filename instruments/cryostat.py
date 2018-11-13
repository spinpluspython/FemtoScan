# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 22:30:31 2018

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
import logging
import serial

from instruments import generic

# logger = logging.getLogger(__name__)


class Cryostat(generic.Instrument):
    """    """

    def __init__(self):
        super(Cryostat, self).__init__()
        self.logger = logging.getLogger('{}.Cryostat'.format(__name__))
        self.logger.info('Created instance of fake Cryostat.')

        self.temperature_current = 300
        self.temperature_target = 300

    def connect(self):
        print('connetcted to fake cryostat. current temperature=' + str(
            self.temperature_current) + '; setted temperature' + str(self.temperature_target))

    def disconnect(self):
        print('Fake cryostat has been disconnected')

    def get_temperature(self):
        self.temperature_current = self.temperature_current + (
                self.temperature_target - self.temperature_current) / 2  # change current temperature closer to the setted.
        print('current temperature ' + str(self.temperature_current))
        time.sleep(.1)
        return (self.temperature_current)

    def set_temperature(self, temperature):
        self.temperature_target = temperature
        print('temperature is setted to' + str(temperature) + '. Wait untill real temperature become desired')

    def change_temperature(self, temperature, tolerance=0.1):
        '''set temperature to the desired Value, wait untll real temperature will become desired and stable. tolerance in kelvin'''
        self.set_temperature(temperature)

        self.check_temp(tolerance)

    def check_temp(self, tolerance, sleep_time=0.1):
        temp = []
        diff = 100000.
        while diff > tolerance:
            time.sleep(sleep_time)
            temp.append(self.get_temperature())
            if len(temp) > 10:
                temp.pop(0)
                diff = max([abs(x - self.temperature_target) for x in temp])
                # diff = abs(self.temperature_current - self.temperature_set)


class MercuryITC(Cryostat):
    def __init__(self):
        super(MercuryITC, self).__init__()
        self.COMPort = 'COM8'
        self.Baud = 115200
        self.ser = serial.Serial()
        self.ser.baudrate = self.Baud
        self.ser.port = self.COMPort

    # %%
    def connect(self):
        '''Set up the the connection with USB to GPIB adapter, opens port, sets up adater for communication with Lokin SR830m
        After using LockInAmplifier use Disconnect function to close the port
        '''
        try:
            self.ser.open()  # opens COM port with values in this class, Opens ones so after using use disconnecnt function to close it
            self.ser.write(b'*IDN?\r\n')  # query version of the temperature controller

            Value = self.ser.readline()  # reads version
            print(Value)


        except Exception as xui:
            print('error' + str(xui))
            self.ser.close()

    def disconnect(self):
        '''Close com port
        '''
        self.ser.close()

    def send_command(self, Command):
        '''Send any command to the opened port in right format.

        '''
        try:
            # self.ser.open()
            self.ser.write((Command + '\r\n').encode('utf-8'))  # xxx.encode() does the same as b'xxx'
            # self.ser.close()
        except:
            print('xui')
            # self.ser.close()

    def read(self, Command):
        '''reads any information from tempereture controller, input command should be query command for tempereture controller, see manual.
        Returns answer from lockin as a byte
        '''
        try:
            # self.ser.open()
            self.send_command(Command)  # query info from device.

            Value = self.ser.readline()  # reads answer
            # self.ser.close()
            return Value
        except Exception as r:
            self.ser.close()
            print(r)

    def writestring(self, SCPICommands):
        '''Transform list of SCPI commands to strig for writing to USB. Adds seporator, transform it to required format. SCPICommands should be list of strings'''
        String = ''
        for item in SCPICommands:
            String = String + item + ':'
        String = String[:-1] + '\r\n'
        return String.encode('utf-8')

    # %%

    def set_temperature(self, temperature):
        '''Sets temperature on the device, temperature should be givet in kelvin.'''
        try:
            command = ['SET', 'DEV', 'MB1.T1', 'TEMP', 'LOOP', 'TSET', str(temperature)]
            self.ser.write(self.writestring(command))
            responce = str(self.ser.readline())
            print(responce)
            # if response.split(sep=':')[-1]='VALID':


        except Exception as xui:
            print('error' + str(xui))
            self.ser.close

    def get_temperature(self, Units='TEMP'):

        try:
            command = ['READ', 'DEV', 'MB1.T1', 'TEMP', 'SIG', Units]
            self.ser.write(self.writestring(command))
            response = self.ser.readline()

            print(response)
            temperature1 = str(response).split(sep=':')[6]
            temperature = float(temperature1[:-5])
            return (temperature)
        except Exception as xui:
            print('error' + str(xui))
            self.ser.close

    # %%


class ITC503s(Cryostat):
    def __init__(self):
        super(ITC503s, self).__init__()
        self.COMPort = 'COM6'  # set on the place
        self.Baud = 9600
        self.deviceAddr = 24
        self.ser = serial.Serial()
        self.ser.timeout = 1
        self.ser.baudrate = self.Baud
        self.ser.port = self.COMPort

    def connect(self):
        """ connect to LockInAmplifier through Prologix USB-GPIB adapter

        Set up the the connection with USB to GPIB adapter, opens port, sets up adater for communication with Lokin SR830m
        After using LockInAmplifier use Disconnect function to close the port
        """
        try:
            self.ser.open()  # opens COM port with values in this class, Opens ones so after using use disconnecnt function to close it
            self.ser.write(
                '++ver\r\n'.encode('utf-8'))  # query version of the prologix USB-GPIB adapter to test connection
            Value = self.ser.readline()  # reads version
            print(Value)
            # self.ser.close()
            self.write('++eoi 0')  # enable the eoi signal mode, which signals about and of the line
            self.write(
                '++eos 1')  # sets up the terminator <cr> wich will be added to every command for LockInAmplifier, this is only for GPIB connetction
            self.write('++addr ' + str(self.deviceAddr))
            self.read('V')
            self.read('C1')
            self.read('A1')
        except Exception as xui:
            print('error' + str(xui))
            self.ser.close()

    def disconnect(self):
        """Close com port
        """
        self.ser.close()

    def write(self, Command):
        """ Send any command to the opened port in right format.

        Comands which started with ++ goes to the prologix adapter, others go directly to device(LockInAmplifier)
        """
        try:
            # self.ser.write('++addr '+str(self.deviceAddr))
            self.ser.write((Command + '\r\n').encode('utf-8'))
            # self.ser.close()
        except Exception as e:
            print('xui>\n{}'.format(e))
            # self.ser.close()

    # %% Reading temperature controller ITC503s functions

    def read(self, command):
        """reads any information from lockin, input command should be query command for lockin, see manual.
        : parameters :
            command: str
                command string to send to lockin
        : return :
            value:
                answer from lockin as byte
        """
        try:
            # self.ser.open()
            self.write('++addr ' + str(self.deviceAddr))
            self.ser.write((command + '\r\n').encode(
                'utf-8'))  # query info from lockin. adapter reads answer automaticaly and store it
            self.ser.write(('++read eoi\r\n').encode(
                'utf-8'))  # query data stored in adapter, eoi means that readin will end as soon as special caracter will recieved. without it will read before timeout, which slow down reading
            value = self.ser.readline()  # reads answer
            # self.ser.close()
            print(value)
            return value

        except Exception as r:
            self.ser.close()
            print(r)

    def set_temperature(self, temperature):
        try:
            command = 'T' + str(temperature)
            self.read(command)
            # self.ser.write(b'++read eoi\r\n')
            response = str(self.ser.readline())
            self.temperature_target = temperature
            print(response)
            # if response.split(sep=':')[-1]='VALID':


        except Exception as xui:
            print('error' + str(xui))
            self.ser.close

    def get_temperature(self):
        try:
            command = 'R1'

            response = str(self.read(command))
            temperature = float(response[3:-3])
            print(temperature)  # todo: change translation procedure
            self.temperature_current = temperature
            # if response.split(sep=':')[-1]='VALID':
            return (temperature)


        except Exception as xui:
            print('error' + str(xui))
            self.ser.close
