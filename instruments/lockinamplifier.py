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
# import sys
# sys.path.append('\\fs02\vgrigore$\Dokumente\program\Spin+python\Instruments\\')
import serial

from instruments import generic
from utilities.units import ureg as u
import numpy as np
import time
import pandas as pd
from configparser import ConfigParser


class LockInAmplifier(generic.Instrument):
    def __init__(self):
        super(LockInAmplifier, self).__init__()

        self.name = 'Fake LockIn Apmlifier'
        self.measurables = [self.read_value]
        self.sensitivity = generic.Parameter(self, value=1, unit=None)
        self.time_constant = generic.Parameter(self, value=0.3, unit=u.second)
        self.sleep_multiplier = 3
        # self.configuration = {'Sensitivity': 0, 'Time constant': 0, 'Reference source': 0,
        #                       'Frequency': 1, 'Reference trigger': 0}
        # self.sensitivity = self.attribute()

    def connect(self):
        print('Fake LockInAmplifier amplifier is connected')

    def disconnect(self):
        print('Fake LockInAmplifier amplifier is disconnected')

    def read_value(self, parameter):
        '''Reads measured value from lockin. Parametr is a string like in manual. 
        except Theta. Che the dictionary of parametrs for Output
        '''
        Value = np.random.rand() # returns value as a string, like the lock-in does
        print(parameter + ' = ' + str(Value) + ' V')
        time.sleep(self.time_constant.value * self.sleep_multiplier)
        return Value


class SR830(LockInAmplifier):

    def __init__(self):
        super().__init__()

        self.GPIB_address = 8
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM6'
        self.ser.timeout = 1


        self.output_dict = {'X': 1, 'Y': 2, 'R': 3, 'Theta': 4, 'Aux in 1': 5, 'Aux in 2': 6, 'Aux in 3': 7,
                            'Aux in 4': 8, 'Reference Frequency': 9, 'CH1 display': 10, 'CH2 diplay': 11}

        self.sensitivity = self.SR830Parameter(self,
                                               codex={'2nV/fA': 0, '5nV/fA': 1, '10nV/fA': 2, '20nV/fA': 3,
                                                      '50nV/fA': 4, '100nV/fA': 5, '200nV/fA': 6, '500nV/fA': 7,
                                                      '1uV/pA': 8, '2uV/pA': 9, '5uV/pA': 10, '10uV/pA': 11,
                                                      '20uV/pA': 12, '50uV/pA': 13, '100uV/pA': 14, '200uV/pA': 15,
                                                      '500uV/pA': 16, '1mV/nA': 17, '2mV/nA': 18, '5mV/nA': 19,
                                                      '10mV/nA': 20, '20mV/nA': 21, '50mV/nA': 22, '100mV/nA': 23,
                                                      '200mV/nA': 24, '500mV/nA': 25, '1V/uA': 26},
                                               value=0,
                                               value_type=int,
                                               cmd='SENS')
        self.time_constant = self.SR830Parameter(self,
                                                 codex={'10us': 0, '30us': 1, '100us': 2, '300us': 3, '1ms': 4,
                                                        '3ms': 5, '10ms': 6, '30ms': 7, '100ms': 8, '300ms': 9,
                                                        '1s': 10, '3s': 11, '10s': 12, '30s': 13, '100s': 14,
                                                        '300s': 15, '1ks': 16, '3ks': 17, '10ks': 18, '30ks': 19},
                                                 value=0,
                                                 value_type=int,
                                                 cmd='OFLT')
        self.low_pass_filter_slope = self.SR830Parameter(self,
                                                         codex={'6 dB': 0, '12 dB': 1, '18 dB': 2, '24 dB': 3},
                                                         value=0,
                                                         value_type=int,
                                                         cmd='OFSL')
        self.input_config = self.SR830Parameter(self,
                                                codex={'A': 0, 'A-B': 1, 'I(1mOm)': 2, 'I(100mOm)': 3},
                                                value=0,
                                                value_type=int,
                                                cmd='ISRC')
        self.input_shield = self.SR830Parameter(self,
                                                codex={'Float': 0, 'Ground': 1},
                                                value=0,
                                                value_type=int,
                                                cmd='IGND')

        self.input_coupling = self.SR830Parameter(self,
                                                  codex={'AC': 0, 'DC': 1},
                                                  value=0,
                                                  value_type=int,
                                                  cmd='ICPL')

        self.input_line_notch_filter = self.SR830Parameter(self,
                                                           codex={'no filters': 0, 'Line notch': 1, '2xLine notch': 2,
                                                                  'Both notch': 3},
                                                           value=0,
                                                           value_type=int,
                                                           cmd='ILIN')
        self.reserve_mode = self.SR830Parameter(self,
                                                codex={'Nigh Reserve': 0, 'Normal': 1, 'Low Noise': 2},
                                                value=0,
                                                value_type=int,
                                                cmd='RMOD')

        self.synchronous_filter = self.SR830Parameter(self,
                                                      codex={'Off': 0, 'below 200Hz': 1},
                                                      value=0,
                                                      value_type=int,
                                                      cmd='SYNC')
        self.phase = self.SR830Parameter(self,
                                         codex={},
                                         value=0,
                                         value_type=int,
                                         cmd='PHAS')
        self.reference_source = self.SR830Parameter(self,
                                                    codex={'internal': 0, 'external': 1},
                                                    value=0,
                                                    value_type=int,
                                                    cmd='FMOD')

        self.frequency = self.SR830Parameter(self,
                                             codex={},
                                             value=1,
                                             value_type=int,
                                             cmd='FREQ')
        self.reference_trigger = self.SR830Parameter(self,
                                                     codex={'Zero crossing': 0, 'Rising edge': 1, 'Falling edge': 2},
                                                     value=0,
                                                     value_type=int,
                                                     cmd='RSPL')
        self.detection_harmonic = self.SR830Parameter(self,
                                                    codex={},
                                                    value=1,
                                                    value_type=int,
                                                    cmd='HARM')
        self.sine_output_amplitude = self.SR830Parameter(self,
                                                       codex={},
                                                       value=2,
                                                       value_type=int,
                                                       cmd='SLVL')
        
        self.sleep_time_dict = {0: 0.00001, 1: 0.00003, 2: 0.0001, 3: 0.0003, 4: 0.001, 5: 0.003, 6: 0.01, 7: 0.03,
                                8: 0.1, 9: 0.3, 10: 1, 11: 3, 12: 10, 13: 30, 14: 100, 15: 300, 16: 1000, 17: 3000}
                                
        self.init_parameters()

    def init_parameters(self):
        self.parameters = {}
        for attr,val in self.__dict__.items():
            if isinstance(getattr(self,attr),generic.Parameter):
                self.parameters[attr] = val

    def get_measurables(self):
        """ return a list of methods which can be used to measure some quantity."""
        return [self.read_snap, self.read_value]

    def get_configuration(self):
        """ get the value of all parameters in current state.

        :returns:
            configDict: dict
                dictionary with as keys the parameter name and as values the
                value in the current configuration.
        """
        configDict = {}
        for item, value in self.parameters.items():
            configDict[item] = value.value
        return configDict

    def set_configuration(self,configDict):
        """ get the value of all parameters in current state.

        :parameter:
            configDict: dict
                dictionary with as keys the parameter name and as values the
                value in the current configuration.
        """
        for key, val in configDict.items():
            assert isinstance(val,SR830.SR830Parameter)
            oldval = self.parameters[key].value
            if oldval != val:
                print('{} changed from {} to {}'.format(key,oldval,val))
                self.parameters[key].value = val

    def save_configuration(self,file):
        """ Save the current configuration to ini file.

        :parameters:
            file: str
                file name complete with absolute path
        """
        configDict = self.get_configuration()
        config = ConfigParser()
        config.add_section('SR830 - Lock-In Amplifier')
        for key, val in configDict.items():
            config.set('SR830 - Lock-In Amplifier', key, str(val))
        if file[-4:] != '.ini':
            file+='.ini'
        with open(file, 'w') as configfile:  # save
            config.write(configfile)

    def load_configuration(self, file): # TODO: fix this, its broken!!
        """ Load a configuration from a previously saved ini file.

        :parameters:
            file: str
                file name complete with absolute path
        """

        config = ConfigParser()
        config.read(file)
        for name in config['SR830 - Lock-In Amplifier']:
            try:
                val = getattr(self,name).type(config['SR830 - Lock-In Amplifier'][name])
                getattr(self,name).value = val
            except AttributeError:
                print('no parameter called {} in this device')


    def is_connected(self):
        """ test if the lock-in amplifier is connected and read/write is allowed.

        :return:
            answer: bool
                True: locking is connected. False: Locking is NOT connected
        """
        try:
            self.ser.write(
                '++ver\r\n'.encode('utf-8'))  # query version of the prologix USB-GPIB adapter to test connection
            val = self.ser.readline()  # reads version
            return True
        except Exception:
            return False

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
            self.write('++eoi 1')  # enable the eoi signal mode, which signals about and of the line
            self.write(
                '++eos 2')  # sets up the terminator <lf> wich will be added to every command for LockInAmplifier, this is only for GPIB connetction
            self.write('++addr'+str(self.GPIB_address))
            self.read('*IDN?')
        except Exception as xui:
            print('error ' + str(xui))
            self.ser.close()

    def disconnect(self):
        """Close com port
        """
        self.ser.close()

    def write(self, Command):
        """ Send any command to the opened port in right format.

        Comands which started with ++ goes to the prologix adapter, others go directly to device(LockInAmplifier)
        """
        assert self.ser.is_open is True, 'COM port closed.'
        try:
            self.ser.write((Command + '\r\n').encode('utf-8'))
        except Exception as e:
            self.disconnect()
            print('writing aborted: error - {}\n COM port closed'.format(e))
            # self.ser.close()

    def read(self, command):
        """reads any information from lockin, input command should be query command for lockin, see manual.
        : parameters :
            command: str
                command string to send to lockin
        : return :
            value:
                answer from lockin as byte
        """
        assert self.ser.is_open is True, 'COM port closed.'

        try:
            # self.ser.open()
            self.write(command)  # query info from lockin. adapter reads answer automaticaly and store it
            self.ser.write(('++read eoi\r\n').encode(
                'utf-8'))  # query data stored in adapter, eoi means that readin will end as soon as special caracter will recieved. without it will read before timeout, which slow down reading
            value = self.ser.readline()  # reads answer
            # self.ser.close()
            print(value)
            return value
            
        except Exception as e:
            self.disconnect()
            print('Reading aborted: error - {}\n COM port closed'.format(e))

    def read_value(self, parameter):
        """Reads measured value from lockin.

        Parametr is a string like in manual. except Theta. Che the dictionary of parametrs for Output

        : parameters :
            Parameter: str
                string for communication as given in the manual.
        : return :
            value:
                ???
        """
        assert parameter in self.output_dict, '{} is not a valid parameter to read from the SR830'.format(parameter)
        Command = 'OUTP ?' + str(self.output_dict[parameter])
        Value = float(self.read(Command))  # returns value as a float
        print(str(Value) + ' V')
        return Value

    def read_snap(self, parameters, format='pandas'):
        """Read chosen Values from LockInAmplifier simultaneously.

        : parameters :
            parameters: list of strings
                Parametrs is a list of strings from outputDict. Sould be at least 2
        :return:
            output: dict or pandas.DataFrame
                according to the format defined with format, will be a dictionary (format='dict')
                or a pandas daraframe (format='pandas')
        """
        assert isinstance(parameters, list), 'parameters need to be a tuple or list'
        assert False not in [isinstance(x, str) for x in parameters], 'items in the list must be strings'
        command = 'SNAP ? '
        for item in parameters:
            # compose command string with parameters in input
            command = command + str(self.output_dict[item]) + ', '
        command = command[:-2]  # cut last ', '
        string = str(self.read(command))[2:-3]  # reads answer, transform it to string, cut system characters
        values = string.split(',')  # split answer to separated values
        if format == 'dict':
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
            print(output)
            return output
        elif format == 'pandas':
            output = pd.DataFrame(data=values, columns=parameters)
            return output
        else:
            print('unknown format {}'.format(format))



    def measure(self, avg=10, sleep=None, var='R'):
        '''Perform one action of mesurements, average signal(canceling function in case of not real values should be implemeted), sleep time could be set manualy or automaticaly sets tim constant of lockin x 3'''
        if sleep == None:
            sleeptime = self.sleep_time_dict[self.time_constant.get()]#TODO 
            sleep = 3 * float(sleeptime)

        signal = []
        time.sleep(sleep)
        for i in range(avg):
            signal.append(self.read_value(var))
            val = sum(signal) / avg
        return val

    def set_to_default(self):
        """ Hardware reset Lock-in Amplifier."""
        self.write('*RST')

    class SR830Parameter(generic.Parameter):
        """ Class for the internal parameters of the lock-in.
        This allows to get and set such parameters."""

        def __init__(self, parent_instrument, **kwargs):
            super().__init__(parent_instrument, **kwargs)
            self.default_value = self.value

        def set(self, value):
            """ set the given value to the Parameter on the lock-in

            :parameters:
                value: str | int
                    value to be set to the Parameter
            """
            if isinstance(value, str):
                command = self.cmd + self.codex[value]
            elif isinstance(value, int) | isinstance(value, float):
                command = self.cmd + str(value)
            else:
                raise ValueError
            self.parent_instrument.write(command)

            if self.CONFIRM_VALUE_IS_SET:
                self.get()

        def get_value(self):
            """ Read the current set value on the Lock-in Amplifier

            :Return:
                value: value returned by the Lock-in Amplifier
            """
            read_cmd = self.cmd + ' ?'
            value = self.parent_instrument.read(read_cmd)

            self.value = self.value_type(value)
            val_str = self.codex[self.value]
            goodstr = ''
            for char in val_str:
                try:
                    int(char)
                    goodstr += char
                except:
                    pass
            return float(goodstr)
            
        def get(self):
            """ Read the current set value on the Lock-in Amplifier

            :Return:
                value: value returned by the Lock-in Amplifier
            """
            read_cmd = self.cmd + ' ?'
            value = self.parent_instrument.read(read_cmd)

            self.value = self.value_type(value)
            return self.value
if __name__ == '__main__':
    # sys.path.append('\\fs02\vgrigore$\Dokumente\program\Spin+python\Instruments\\')

    pass