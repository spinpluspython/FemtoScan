# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 17:11:24 2018

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

import numpy as np
import serial

from instruments import generic
from utilities.exceptions import DeviceNotConnectedError
from utilities.settings import parse_setting


class LockInAmplifier(generic.Instrument):
    __verbose = parse_setting('general', 'verbose')

    def __init__(self):
        super(LockInAmplifier, self).__init__()

        self.name = 'Fake LockIn Apmlifier'
        # list all methods which can be used as measurement functions
        self.measurables = ['read_value']
        self.sleep_multiplier = 3
        self._settings = {}

    def connect(self):
        print('Fake LockInAmplifier amplifier is connected')

    def disconnect(self):
        print('Fake LockInAmplifier amplifier is disconnected')

    def read_value(self, parameter):
        '''Reads measured value from lockin. Parametr is a string like in manual. 
        except Theta. Che the dictionary of parametrs for Output
        '''
        Value = np.random.rand()  # returns value as a string, like the lock-in does
        print(parameter + ' = ' + str(Value) + ' V')
        time.sleep(self.time_constant.value * self.sleep_multiplier)
        return Value

    @property
    def connected(self):
        return True

    def measure(self, parameters, return_dict=False):

        if parameters == 'default':
            parameters = ['X', 'Y', 'Aux1', 'Aux2', 'Aux3', 'Aux4']
        assert self.connected, 'lockin not connected.'
        # sleep for the defined dwell time
        time.sleep(self.time_constant.value * self.sleep_multiplier)
        values = list(np.random.randn(len(parameters)))

        if return_dict:
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
            if self.__verbose: print(output)
            return output
        else:
            return values


class SR830_oldparameters(LockInAmplifier):

    def __init__(self):
        super().__init__()
        self.name = 'SR830 Lockin Amplifier'

        self.sleep_multiplier = 3

        # Connectivity:
        self.GPIB_address = 8
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM6'
        self.ser.timeout = 1

        self.output_dict = {'X': 1, 'Y': 2, 'R': 3, 'Theta': 4, 'Aux1': 5, 'Aux2': 6, 'Aux3': 7,
                            'Aux4': 8, 'Reference Frequency': 9, 'CH1 display': 10, 'CH2 diplay': 11}

        # parameters:

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
        for attr, val in self.__dict__.items():
            if isinstance(getattr(self, attr), generic.Parameter):
                self.parameters[attr] = val

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
            self.write('++addr' + str(self.GPIB_address))
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

    def measure(self, parameters='default', format='dict'):
        """ Measure the parameters in the current state

        Args:
            parameters:
            format (str): return format for this function. 'dict', generates a
                dictionary with parameters as keys. 'list' returns a list
                containing the values.
        Returns:
            output (dict): if format='dict'. keys are the parameter names,
                values are floats representing the numbers returned by the
                lockin
            list (list): list of float values as returned by the lockin.
        """
        if parameters == 'default':
            parameters = ['X', 'Y', 'Aux1', 'Aux2', 'Aux3', 'Aux4']

        assert self.is_connected(), 'lockin not connected.'
        # sleep for the defined dwell time
        time.sleep(self.time_constant.get() * self.sleep_multiplier)

        values = self.read_snap(parameters)

        if format not in ('dict'):
            return values
        else:
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
            if self.__verbose: print(output)
            return output

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
        if self.__verbose: print(str(Value) + ' V')
        return Value

    def read_snap(self, parameters):
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
        assert 2 <= len(parameters) <= 6, 'read_snap requires 2 to 6 parameters'
        command = 'SNAP ? '
        for item in parameters:
            # compose command string with parameters in input
            command = command + str(self.output_dict[item]) + ', '
        command = command[:-2]  # cut last ', '
        string = str(self.read(command))[2:-3]  # reads answer, transform it to string, cut system characters
        values = [float(x) for x in string.split(',')]  # split answer to separated values and turn them to floats
        return values

    def measure_avg(self, avg=10, sleep=None, var='R'):
        ''' [DEPRECATED] Perform one action of mesurements, average signal(canceling function in case of not real values should be implemeted), sleep time could be set manualy or automaticaly sets tim constant of lockin x 3'''
        if sleep == None:
            sleeptime = self.sleep_time_dict[self.time_constant.get()]  # TODO
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


class SR830(LockInAmplifier):

    def __init__(self):
        super().__init__()
        self.name = 'SR830 Lockin Amplifier'
        self._settings = {
            'sensitivity': {'value': 2E-9,
                            'allowed_values': [2E-9, 5E-9, 1E-8, 2E-8, 5E-8, 1E-7,
                                               2E-7, 5E-7, 1E-6, 2E-6, 5E-6, 1E-5,
                                               2E-5, 5E-5, 1E-4, 2E-4, 5E-4, 1E-3,
                                               2E-3, 5E-3, 1E-2, 2E-2, 5E-2, 1E-1,
                                               2E-1, 5E-1, 1.],
                            'unit': 'V or A',
                            'cmd': 'SENS',
                            },
            'time_constant': {'value': 3E-1,
                              'allowed_values': [1E-5, 3e-5, 1E-4, 3e-4, 1E-3, 3e-3,
                                                 1E-2, 3e-2, 1E-1, 3e-1, 1., 3.,
                                                 1E1, 3e1, 1E2, 3e2, 1E3, 3e3, 1E4, 3E4],
                              'unit': 's',
                              'cmd': 'OFLT',
                              },
            'low_pass_filter_slope': {'value': 6,
                                      'allowed_values': [6, 12, 18, 24],
                                      'unit': 'dB',
                                      'cmd': 'OFSL',
                                      },
            'input_config': {'value': 'A',
                             'allowed_values': ['A', 'A-B', 'I(1mOm)', 'I(100mOm)'],
                             'unit': '',
                             'cmd': 'OFSL',
                             },
            'input_shield': {'value': 'Float',
                             'allowed_values': ['Float', 'Ground'],
                             'unit': '',
                             'cmd': 'IGND',
                             },
            'input_coupling': {'value': 'AC',
                               'allowed_values': ['AC', 'DC'],
                               'unit': '',
                               'cmd': 'ICPL',
                               },
            'input_line_notch_filter': {'value': 'AC',
                                        'allowed_values': ['no filters', 'Line notch',
                                                           '2xLine notch', 'Both notch'],
                                        'unit': '',
                                        'cmd': 'ILIN',
                                        },
            'reserve_mode': {'value': 'High Reserve',
                             'allowed_values': ['High Reserve', 'Normal', 'Low Noise'],
                             'unit': '',
                             'cmd': 'RMOD',
                             },
            'synchronous_filter': {'value': 'Off',
                                   'allowed_values': ['Off', 'Below 200Hz'],
                                   'unit': '',
                                   'cmd': 'SYNC',
                                   },
            'phase': {'value': 0.,
                      'allowed_values': None,
                      'unit': '',
                      'cmd': 'PHAS',
                      },
            'reference_source': {'value': 'Off',
                                 'allowed_values': ['Internal', 'External'],
                                 'unit': '',
                                 'cmd': 'FMOD',
                                 },
            'frequency': {'value': 1.,
                          'allowed_values': None,
                          'unit': '',
                          'cmd': 'FREQ',
                          },
            'reference_trigger': {'value': 'Zero crossing',
                                  'allowed_values': ['Zero crossing', 'Rising edge', 'Falling edge'],
                                  'unit': '',
                                  'cmd': 'RSPL',
                                  },
            'detection_harmonic': {'value': 1,
                                   'allowed_values': None,
                                   'unit': '',
                                   'cmd': 'HARM',
                                   },
            'sine_output_amplitude': {'value': 2,
                                      'allowed_values': ['Zero crossing', 'Rising edge', 'Falling edge'],
                                      'unit': '',
                                      'cmd': 'SLVL',
                                      },

        }

        self.sleep_multiplier = 3

        # Connectivity:
        self.GPIB_address = 8
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM6'
        self.ser.timeout = 1

        # settings
        self.should_sync = True  # to keep track if all settings are up to date with device state
        self._channel_names = ['X', 'Y', 'R', 'Theta', 'Aux1', 'Aux2', 'Aux3',
                               'Aux4', 'Reference Frequency', 'CH1 display',
                               'CH2 diplay']

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
            self.write('++addr' + str(self.GPIB_address))
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
        if not self.ser.is_open():
            raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        try:
            self.ser.write((Command + '\r\n').encode('utf-8'))
        except Exception as e:
            self.disconnect()
            print('Couldnt write command: error - {}\n'.format(e))

    def read(self, command):
        """reads any information from lockin, input command should be query command for lockin, see manual.
        : parameters :
            command: str
                command string to send to lockin
        : return :
            value:
                answer from lockin as byte
        """
        if not self.is_connected():
            self.connect()
            raise DeviceNotConnectedError('COM port is closed. Device is not connected.')

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
            print('Couldnt read command:: error - {}\n'.format(e))

    def set_to_default(self):
        """ Hardware reset Lock-in Amplifier."""
        if not self.ser.is_open:
            raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        self.write('*RST')

    # %% measurement methods
    def measure(self, parameters='default', return_dict='dict'):
        """ Measure the parameters in the current state

        Args:
            parameters:
            format (str): return format for this function. 'dict', generates a
                dictionary with parameters as keys. 'list' returns a list
                containing the values.
        Returns:
            output (dict): if format='dict'. keys are the parameter names,
                values are floats representing the numbers returned by the
                lockin
            list (list): list of float values as returned by the lockin.
        """

        if not self.is_connected: self.connect()
        if parameters == 'default':
            parameters = ['X', 'Y', 'Aux1', 'Aux2', 'Aux3', 'Aux4']

#        assert self.is_connected(), 'lockin not connected.'
        # sleep for the defined dwell time
        time.sleep(self.time_constant * self.sleep_multiplier)

        values = self.read_snap(parameters)

        
        if return_dict:
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
            if self.__verbose: print(output)
            return output
        else:
            return values

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
        if self.__verbose: print(str(Value) + ' V')
        return Value

    def read_snap(self, parameters):
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
        assert 2 <= len(parameters) <= 6, 'read_snap requires 2 to 6 parameters'
        command = 'SNAP ? '
        for item in parameters:
            # compose command string with parameters in input
            command = command + str(self._channel_names.index(item)) + ', '
        command = command[:-2]  # cut last ', '
        string = str(self.read(command))[2:-3]  # reads answer, transform it to string, cut system characters
        values = [float(x) for x in string.split(',')]  # split answer to separated values and turn them to floats
        return values

    def measure_avg(self, avg=10, sleep=None, var='R'):
        ''' [DEPRECATED] Perform one action of mesurements, average signal(canceling function in case of not real values should be implemeted), sleep time could be set manualy or automaticaly sets tim constant of lockin x 3'''
        if sleep == None:
            sleeptime = self.time_constant  # TODO
            sleep = 3 * float(sleeptime)

        signal = []
        time.sleep(sleep)
        for i in range(avg):
            signal.append(self.read_value(var))
            val = sum(signal) / avg
        return val

    # %% settings property generators:

    # for key,value in self._settings.items()

    @property
    def sensitivity(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'sensitivity'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @sensitivity.setter
    def sensitivity(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'sensitivity'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def time_constant(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'time_constant'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @time_constant.setter
    def time_constant(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'time_constant'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def low_pass_filter_slope(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'low_pass_filter_slope'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @low_pass_filter_slope.setter
    def low_pass_filter_slope(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'low_pass_filter_slope'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def input_config(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_config'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_config.setter
    def input_config(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_config'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def input_shield(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_shield'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_shield.setter
    def input_shield(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_shield'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def input_coupling(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_coupling'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_coupling.setter
    def input_coupling(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_coupling'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def input_line_notch_filter(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_line_notch_filter'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_line_notch_filter.setter
    def input_line_notch_filter(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_line_notch_filter'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def reserve_mode(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reserve_mode'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reserve_mode.setter
    def reserve_mode(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reserve_mode'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def synchronous_filter(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'synchronous_filter'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @synchronous_filter.setter
    def synchronous_filter(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'synchronous_filter'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def reference_source(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reference_source'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reference_source.setter
    def reference_source(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reference_source'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def reference_trigger(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reference_trigger'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reference_trigger.setter
    def reference_trigger(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reference_trigger'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def sine_output_amplitude(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'sine_output_amplitude'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @sine_output_amplitude.setter
    def sine_output_amplitude(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'sine_output_amplitude'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def detection_harmonic(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'detection_harmonic'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            # value = self._settings[setting]['allowed_values'][value_idx]
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @detection_harmonic.setter
    def detection_harmonic(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'detection_harmonic'
        assert isinstance(value, float), 'wrong type for detection harmonic'

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def frequency(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'frequency'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @frequency.setter
    def frequency(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'frequency'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value

    @property
    def phase(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'phase'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @phase.setter
    def phase(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'phase'
        assert value in self._settings[setting]['allowed_values']

        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            self._settings[setting]['value'] = value
        except DeviceNotConnectedError:
            print('Device not connected: storing value locally and queuing to write on device once conneceted.')
            self.should_sync = True
            self._settings[setting]['value'] = value


if __name__ == '__main__':
    # sys.path.append('\\fs02\vgrigore$\Dokumente\program\Spin+python\Instruments\\')

    pass
