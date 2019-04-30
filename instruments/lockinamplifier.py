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
import logging
import time

import numpy as np
import serial

import os
os.chdir('U:\\Dokumente\program\Spin+python\Instruments\instruments')
import generic
#os.chdir('U:\\Dokumente\program\Spin+python\Instruments\utilities')
#import DeviceNotConnectedError
#import parse_setting


class LockInAmplifier(generic.Instrument):
    #__verbose = parse_setting('general', 'verbose')

    def __init__(self):
        super(LockInAmplifier, self).__init__()
        self.logger = logging.getLogger('{}.LockInAmplifier'.format(__name__))
        self.logger.info('Created instance of fake LockInAmplifier.')

        self.name = 'Fake LockIn Apmlifier'
        # list all methods which can be used as measurement functions
        self.measurables = ['read_value']
        self._dwell_time_factor = 3
        self._settings = {'time_constant': {'value': .1}}
        self._version = 'Fake lockin 0.1'

    def connect(self):
        self._connected = True
        self.logger.info('Connected Fake LockInAmplifier amplifier.')

    def disconnect(self):
        self._connected = False
        self.logger.info('Disconnected Fake LockInAmplifier amplifier.')

    def read_value(self, parameter):
        """ emulates the read_value method from SR830"""
        self.logger.debug('attempting to read value from Fake lokin')
        Value = np.random.rand()  # returns value as a string, like the lock-in does
        print(parameter + ' = ' + str(Value) + ' V')
        time.sleep(self.time_constant.value * self._dwell_time_factor)
        self.logger.debug('Fake lokin reading complete')
        return Value

    @property
    def dwell_time_factor(self):
        return self._dwell_time_factor

    @dwell_time_factor.setter
    def dwell_time_factor(self, val):
        assert val > 0, "cannot wait for negative times! travelling back in time!"
        self.logger.debug('Dwell time set to {}'.format(val))
        self._dwell_time_factor = val

    @property
    def dwell_time(self):
        return self.time_constant * self._dwell_time_factor

    @property
    def time_constant(self):
        return self._settings['time_constant']['value']

    @time_constant.setter
    def time_constant(self, val):
        assert val > 0, 'Time constant cannot be negative.'
        self._settings['time_constant']['value'] = val

    def measure(self, parameters, return_dict=False):

        if parameters == 'default':
            parameters = ['X', 'Y', 'Aux1', 'Aux2', 'Aux3', 'Aux4']
        assert self.connected, 'lockin not connected.'
        self.logger.debug(
            'Measuring (fake) parameters {}, returning {}'.format(parameters, 'dict' if return_dict else 'list'))
        # sleep for the defined dwell time

        self.logger.debug('waiting dwell time of {}'.format(self.dwell_time))
        time.sleep(self.dwell_time)
        # self.logger.debug('Generating random values for each parameter.')
        values = list(np.random.randn(len(parameters)))
        # self.logger.debug('Values generated: {}'.format(values))
        if return_dict:
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
            # self.logger.debug('Measured output: {}'.format(output))
            return output
        else:
            return values


class SR830(LockInAmplifier):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('{}.SR830'.format(__name__))
        self.logger.info('Created instance of SR830 Lock-In Amplifier.')

        self.name = 'SR830 Lock-In Amplifier'
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

        # Connectivity:
        self.GPIB_address = 8
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM6'
        self.ser.timeout = 1

        # settings
        self.should_sync = True  # to keep track if all settings are up to date with device state
        self.output_dict = {'X': 1, 'Y': 2, 'R': 3, 'Theta': 4, 'Aux1': 5, 'Aux2': 6, 'Aux3': 7,
                            'Aux4': 8, 'Reference Frequency': 9, 'CH1 display': 10, 'CH2 diplay': 11}
        self._channel_names = ['X', 'Y', 'R', 'Theta', 'Aux1', 'Aux2', 'Aux3',
                               'Aux4', 'Reference Frequency', 'CH1 display',
                               'CH2 diplay']

    @property
    def connected(self):
        """ test if the lock-in amplifier is connected and read/write is allowed.

        :return:
            answer: bool
                True: locking is connected. False: Locking is NOT connected
        """
        self.logger.debug('testing if lockin is connected and responds.')
        if self._connected:
            try:
                self.ser.write(
                    '++ver\r\n'.encode('utf-8'))  # query version of the prologix USB-GPIB adapter to test connection
                val = self.ser.readline()  # reads version
                self.logger.debug('SR830 Lockin is Connected')
                return True
            except Exception:
                self.logger.critical('Lockin unexpectedly disconnected!!')
                return False
        else:
            self.logger.debug('SR830 Lockin is NOT connected')
            return False

    def connect(self):
        """ connect to LockInAmplifier through Prologix USB-GPIB adapter

        Set up the the connection with USB to GPIB adapter, opens port, sets up adater for communication with Lokin SR830m
        After using LockInAmplifier use Disconnect function to close the port
        """
        self.logger.debug(
            'attempting to connect to SR830 through Prologix adapter. port:{}, GPIB:{}'.format(self.ser.port,
                                                                                               self.GPIB_address))
        try:
            self.ser.open()  # opens COM port with values in this class, Opens ones so after using use disconnecnt function to close it
            self.logger.debug('serial open')
            self.ser.write(
                '++ver\r\n'.encode('utf-8'))  # query version of the prologix USB-GPIB adapter to test connection
            value = self.ser.readline()  # reads version
            self.logger.info('Encoder version: {}'.format(value))
            # self.ser.close()
            self.write('++eoi 1')  # enable the eoi signal mode, which signals about and of the line
            self.write(
                '++eos 2')  # sets up the terminator <lf> wich will be added to every command for LockInAmplifier, this is only for GPIB connetction
            self.write('++addr' + str(self.GPIB_address))
            self.logger.debug('assigned GPIB address to {}'.format(self.GPIB_address))
            idn = self.read('*IDN?')
            self.logger.debug('IDN response from lockin: {}'.format(idn))
            self._connected = True
        except Exception as e:
            self.ser.close()
            self.logger.error('Connection Error: {} - Closing serial port'.format(e), exc_info=True)

    def disconnect(self):
        """Close com port
        """
        self.logger.info('closing serial port')
        self._connected = False
        self.ser.close()
        self.logger.debug('SR830 disconnected.')

    def write(self, Command):
        """ Send any command to the opened port in right format.

        Comands which started with ++ goes to the prologix adapter, others go directly to device(LockInAmplifier)
        """
        if not self.ser.isOpen():
            raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        try:
            self.ser.write((Command + '\r\n').encode('utf-8'))
        except Exception as e:
            self.disconnect()
            self.logger.error('Couldnt write command: error - {}\n'.format(e), exc_info=True)

    def read(self, command):
        """reads any information from lockin, input command should be query command for lockin, see manual.
        : parameters :
            command: str
                command string to send to lockin
        : return :
            value:
                answer from lockin as byte
        """
        if not self.connected: raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        try:
            # query info from lockin. adapter reads answer automaticaly and store it
            self.write(command)
            # query data stored in adapter, eoi means that readin will end as
            # soon as special caracter will recieved.  without it will read
            # before timeout, which slow down reading
            self.ser.write(('++read eoi\r\n').encode('utf-8'))
            value = self.ser.readline()  # reads answer
            self.logger.debug('serial response: {}'.format(value))
            return value

        except Exception as e:
            self.disconnect()
            self.logger.error('Couldnt read command:: error - {}\n'.format(e), exc_info=True)

    def set_to_default(self):
        """ Hardware reset Lock-in Amplifier."""
        if not self.ser.is_open:
            raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        self.write('*RST')

    # measurement methods
    def measure(self, parameters='default', return_dict=True):
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

        if not self.connected: raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
        if parameters == 'default':
            parameters = ['X', 'Y', 'Aux1', 'Aux2', 'Aux3', 'Aux4']
        # calculate sleep time from memory, without asking the lockin.+
        dwell = self.get_setting('time_constant') * self._dwell_time_factor
        self.logger.info('Lockin dwelling {}s'.format(dwell))
        time.sleep(dwell)

        values = self.read_snap(parameters)

        if return_dict:
            output = {}
            for idx, item in enumerate(parameters):
                output[item] = float(values[idx])  # compose dictionary of values(float)
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
            value: float
                value output by the lockin
        """
        assert parameter in self.output_dict, '{} is not a valid parameter to read from the SR830'.format(parameter)
        Command = 'OUTP ?' + str(self.output_dict[parameter])
        Value = float(self.read(Command))  # returns value as a float
        print(str(Value) + ' V')
        return Value

    def read_snap(self, parameters):
        """Read chosen Values from LockInAmplifier simultaneously.

        : parameters :
            parameters: list of strings
                Parameters is a list of strings from outputDict. Should be at least 2
        :return:
            output: list of float
                list corresponding in position to the parameters given.
        """
        if not self.connected: raise DeviceNotConnectedError('COM port is closed. Device is not connected.')
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
        self.logger.info('Read_Snap: {} for {}'.format(values, parameters))
        return values

    def measure_avg(self, avg=10, sleep=None, var='R'):
        ''' [DEPRECATED] Perform one action of mesurements, average signal(canceling function in case of not real values should be implemeted), sleep time could be set manualy or automaticaly sets tim constant of lockin x 3'''
        self.logger.warning('[DEPRECATED] Using method "measure_avg" which is Deprecated')

        if sleep == None:
            sleeptime = self.time_constant
            sleep = 3 * float(sleeptime)

        signal = []
        time.sleep(sleep)
        for i in range(avg):
            signal.append(self.read_value(var))
            val = sum(signal) / avg
        return val

    # settings property generators:
    @property
    def sensitivity(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'sensitivity'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @sensitivity.setter
    def sensitivity(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'sensitivity'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def time_constant(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'time_constant'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
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
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def low_pass_filter_slope(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'low_pass_filter_slope'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @low_pass_filter_slope.setter
    def low_pass_filter_slope(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'low_pass_filter_slope'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def input_config(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_config'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_config.setter
    def input_config(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_config'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def input_shield(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_shield'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_shield.setter
    def input_shield(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_shield'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def input_coupling(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_coupling'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_coupling.setter
    def input_coupling(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_coupling'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def input_line_notch_filter(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'input_line_notch_filter'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @input_line_notch_filter.setter
    def input_line_notch_filter(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'input_line_notch_filter'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def reserve_mode(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reserve_mode'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reserve_mode.setter
    def reserve_mode(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reserve_mode'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def synchronous_filter(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'synchronous_filter'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @synchronous_filter.setter
    def synchronous_filter(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'synchronous_filter'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def reference_source(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reference_source'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reference_source.setter
    def reference_source(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reference_source'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def reference_trigger(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'reference_trigger'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @reference_trigger.setter
    def reference_trigger(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'reference_trigger'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def sine_output_amplitude(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'sine_output_amplitude'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value_idx = int(self.read(command))
            value = self._settings[setting]['allowed_values'][value_idx]
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @sine_output_amplitude.setter
    def sine_output_amplitude(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'sine_output_amplitude'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def detection_harmonic(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'detection_harmonic'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
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
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def frequency(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'frequency'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @frequency.setter
    def frequency(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'frequency'
        assert isinstance(value, float), 'wrong type for detection harmonic'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value

    @property
    def phase(self):
        """ return the value on lockin or if disconnected the locally set value"""
        setting = 'phase'
        try:
            command = self._settings[setting]['cmd'] + '?'
            value = float(self.read(command))
            old_value = self._settings[setting]['value']
            if old_value != value:
                self._settings[setting]['value'] = value
                self.logger.debug(
                    'Local value of {} changed to remote value: was {}, now is {}'.format(setting, old_value, value))
        except DeviceNotConnectedError:
            self.logger.warning('Device not connected: returning stored value')
            value = self._settings[setting]['value']
        return value

    @phase.setter
    def phase(self, value):
        """ Set the value on the lockin or if disconnected queue it to be set."""
        setting = 'phase'
        assert isinstance(value, float), 'wrong type for detection harmonic'
        try:
            cmd = self._settings[setting]['cmd']
            cmd += str(self._settings[setting]['allowed_values'].index(value))
            self.write(cmd)
            old_val = self._settings[setting]['value']
            self._settings[setting]['value'] = value
            self.logger.debug('Local AND Remote value of {} changed from {} '
                              'to {}'.format(setting, old_val, value))
        except DeviceNotConnectedError:
            self.should_sync = True
            self.logger.warning('Device not connected, couldnt set value remotely.'
                                '\n Local value of {} changed from {} '
                                'to {}\n'.format(setting, old_val, value))
            self._settings[setting]['value'] = value


if __name__ == '__main__':
    # sys.path.append('\\fs02\vgrigore$\Dokumente\program\Spin+python\Instruments\\')

    pass
