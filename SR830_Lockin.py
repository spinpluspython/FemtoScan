# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 14:52:50 2017

@author: vgrigore
"""

import serial
import time
import Lockin
class SR830(Lockin.Lockin):
    
    def __init__(self):
        self.COMPort='COM6'
        self.Baud=115200
        self.deviceAddr=8
        self.ser=serial.Serial()
        self.ser.baudrate=self.Baud
        self.ser.port=self.COMPort
        self.sensetivity_dict={'2nV/fA':0,'5nV/fA':1,'10nV/fA':2,'20nV/fA':3,'50nV/fA':4,'100nV/fA':5,
                       '200nV/fA':6,'500nV/fA':7,'1uV/pA':8,'2uV/pA':9,'5uV/pA':10,'10uV/pA':11,'20uV/pA':12,
                       '50uV/pA':13,'100uV/pA':14,'200uV/pA':15,'500uV/pA':16,'1mV/nA':17,'2mV/nA':18,
                       '5mV/nA':19,'10mV/nA':20,'20mV/nA':21,'50mV/nA':22,'100mV/nA':23,'200mV/nA':24,
                       '500mV/nA':25,'1V/uA':26}
        
        self.output_dict={'X':1,'Y':2,'R':3,'Theta':4,'Aux in 1':5,'Aux in 2':6,'Aux in 3':7,
                    'Aux in 4':8,'Reference Frequency':9,'CH1 display': 10,'CH2 diplay': 11}
        
        self.time_constant_dict={'10us':0,'30us':1,'100us':2,'300us':3,'1ms':4,'3ms':5,
                            '10ms':6,'30ms':7,'100ms':8,'300ms':9,'1s':10,'3s':11,
                            '10s':12,'30s':13,'100s':14,'300s':15,'1ks':16,'3ks':17,
                            '10ks':18,'30ks':19}
        
        self.low_pass_filter_slope_dict={'6 dB':0, '12 dB':1, '18 dB':2, '24 dB':3}
        
        self.input_config={'A':0,'A-B':1,'I(1mOm)':2,'I(100mOm)':3}
        
        self.input_shield={'Float':0,'Ground':1}
        
        self.input_coupling={'AC':0,'DC':1}
        
        self.input_line_notch_filter={'no filters':0,'Line notch':1,'2xLine notch':2,'Both notch':3}
        
        self.reserve_mode={'Nigh Reserve':0, 'Normal':1,'Low Noise':2}
        
        self.synchronous_filter={'Off':0,'below 200Hz':1}
        
        self.reference_source={'internal':0,'external':1}
        
        self.reference_trigger={'Zero crossing':0,'Rising edge':1,'Falling edge':2}
        
        self.configuration={'Sensitivity':0,'Time constant':0,'Low pass filter slope':0,'Input configuration':0,'Input shield':0,
                            'Input coupling':0, 'Input notch filter':0, 'Reserve mode':0,'Synchronous filter':0,'Reference source':0,
                            'Frequency':1,'Reference trigger':0,'Detection harmonic':1,'Sine output amplitude':2}
        
#%% conection to Prologix USB-GPIB adapter

    def connect(self):
        '''Set up the the connection with USB to GPIB adapter, opens port, sets up adater for communication with Lokin SR830m
        After using Lockin use Disconnect function to close the port
        '''
        try:    
            self.ser.open() # opens COM port with values in this class, Opens ones so after using use disconnecnt function to close it
            self.ser.write('++ver\r\n'.encode('utf-8')) # query version of the prologix USB-GPIB adapter to test connection
            Value=self.ser.readline() # reads version
            print(Value)
            #self.ser.close()
            self.sendCommand('++eoi 1') # enable the eoi signal mode, which signals about and of the line
            self.sendCommand('++eos 2') # sets up the terminator <lf> wich will be added to every command for Lockin, this is only for GPIB connetction
        except Exception as xui: 
            print('error'+str(xui))
            self.ser.close()   
            
    def disconnect(self):
        '''Close com port
        '''
        self.ser.close()
        
    def write(self,Command):
        '''Send any command to the opened port in right format. 
        Comands which started with ++ goes to the prologix adapter, others go directly to device(Lockin)
        '''
        try:
            #self.ser.open()
            self.ser.write((Command+'\r\n').encode('utf-8'))
            #self.ser.close()
        except: 
            print('xui')
            #self.ser.close()
            
#%% Reading Lockin SR830 functions
    
    def read(self, Command):
        '''reads any information from lockin, input command should be query command for lockin, see manual.
        Returns answer from lockin as a byte
        '''
        try:
            #self.ser.open()
            self.ser.write((Command+'\r\n').encode('utf-8')) # query info from lockin. adapter reads answer automaticaly and store it
            self.ser.write(('++read eoi\r\n').encode('utf-8')) # query data stored in adapter, eoi means that readin will end as soon as special caracter will recieved. without it will read before timeout, which slow down reading
            Value=self.ser.readline() # reads answer
            #self.ser.close()
            return Value 
        except Exception as r:
            self.ser.close()
            print(r)
            
    def read_value(self,parameter):
        '''Reads measured value from lockin. Parametr is a string like in manual. 
        except Theta. Che the dictionary of parametrs for Output
        '''
        Command='OUTP ?' + str(self.output_dict[parameter])
        Value=float(self.read(Command)) # returns value as a float 
        print(str(Value)+' V')
        return Value
        
    def readSnap(self, parametrs):
        '''Read chosen Values from Lokin simultaniously. returns dictionary of values. 
        Parametrs is a list of strings from outputDict. Sould be at least 2
        '''
        command='SNAP ? '
        for item in parametrs:
            command=command + str(self.output_dict[item]) + ', ' # compose command string with parametrs in input
        command=command[:-2] # cut last ', ' 
        string=str(self.read(command))[2:-3] #reads answer, transform it to string, cut system characters
        values=string.split(',') # split answer to separated values
        output={}
        for idx, item in enumerate(parametrs): 
            output[item]=float(values[idx]) # compose dictionary of values(float)
        print(output)
        return output
        
#%% Set parametrs functions
        
    def set_to_default(self):
        '''Reset lockin
        '''
        self.write('*RST')
    
    def set_sensitivity(self, sens):
        '''Sets the sensitivity on SR830 Lock in. sens is string like on the front panel, mk=u
        '''
        if type(sens)==str:
            command='SENS'+str(self.sensetivity_dict[sens])
        else:
            command='SENS'+str(sens)
        self.write(command)
        self.get_sensitivity()
        
        
    def set_time_constant(self, timeConst):
        '''Sets the Time Constant on SR830 Lock in. sens is string like on the front panel, mk=u
        '''
        if type(timeConst)==str:
            command='OFLT'+str(self.time_constant_dict[timeConst])
        else:
            command='OFLT'+str(timeConst)
        self.write(command)
        self.get_time_constant()
    
    def set_low_pass_filter_slope(self, LPFilt):
        '''Sets the low pass filter slope on SR830 Lock in. sens is string like on the front panel
        '''
        if type(LPFilt)==str:    
            command='OFSL'+str(self.low_pass_filter_slope_dict[LPFilt])
        else:
            command='OFSL'+str(LPFilt)
        self.write(command)
        self.get_low_pass_filter_slope()
        
    def set_input_config(self, config):
        if type(config)==str:    
            command='ISRC'+str(self.input_config[config])
        else:
            command='ISRC'+str(config)
        self.write(command)
        self.get_input_config()
    
    def set_input_shield(self, shield):
        if type(shield)==str:    
            command='IGND'+str(self.input_shield[shield])
        else:
            command='IGND'+str(shield)
        self.write(command)
        self.get_input_shield()
        
    def set_input_coupling(self, coupling):
        if type(coupling)==str:    
            command='ICPL'+str(self.input_coupling[coupling])
        else:
            command='ICPL'+str(coupling)
        self.write(command)
        self.get_input_coupling()
    
    def set_input_notch_filter(self, notchFilter):
        if type(notchFilter)==str:
            command='ILIN'+str(self.input_line_notch_filter[notchFilter])
        else:
            command='ILIN'+str(notchFilter)
        self.write(command)
        self.get_input_notch_filter()
        
    def set_reserve_mode(self, mode):
        if type(mode)==str:
            command='RMOD'+str(self.reserve_mode[mode])
        else:
            command='RMOD'+str(mode)
        self.write(command)
        self.get_reserve_mode()
    
    def set_synchronous_filter(self, synchronousFilter):
        if type(synchronousFilter)==str:    
            command='SYNC'+str(self.synchronous_filter[synchronousFilter])
        else:
            command='SYNC'+str(synchronousFilter)
        self.write(command)
        self.get_synchronous_filter()
        
    def set_phase(self, phase):
        command='PHAS'+str(phase)
        self.write(command)
        self.get_phase()
    
    def set_reference_source(self, source):
        if type(source)==str:    
            command='FMOD'+str(self.reference_source[source])
        else:
            command='FMOD'+str(source)
        self.write(command)
        self.get_reference_source()
    
    def set_frequency(self, freq):
        command='FREQ'+str(freq)
        self.write(command)
        self.get_frequency()
    
    def set_reference_trigger(self, refTrigger):
        if type(refTrigger)==str:    
            command='RSPL'+str(self.reference_trigger[refTrigger])
        else:
            command='RSPL'+str(refTrigger)
        self.write(command)
        self.get_reference_trigger()
        
    def set_harmonic(self,harm):
        '''sets detection harmonic, harm is integer drom 1 to 19999
        '''
        command='HARM'+str(harm)
        self.write(command)
        self.get_harmonic()
   
    def set_sine_output_amplitude(self,ampl):
        '''setsthe amplitude of the sine output. Value of ampl is a voltage in Volts 0.004<=ampl<=5
        '''
        command='SLVL'+str(ampl)
        self.write(command)
        self.get_sine_output_amplitude()
        
#%% Get parameters function
    
    def get_sensitivity(self):
        self.configuration['Sensitivity']=int(self.read('SENS ?'))
        
    def get_time_constant(self):
        self.configuration['Time constant']=int(self.read('OFLT ?'))
        
    def get_low_pass_filter_slope(self):
        self.configuration['Low pass filter slope']=int(self.read('OFSL ?'))
        
    def get_input_config(self):
        self.configuration['Input configuration']=int(self.read('ISRC ?'))
        
    def get_input_shield(self):
        self.configuration['Input shield']=int(self.read('IGND ?'))
        
    def get_input_coupling(self):
        self.configuration['Input coupling']=int(self.read('ICPL ?'))
        
    def get_input_notch_filter(self):
        self.configuration['Input notch filter']=int(self.read('ILIN ?'))
        
    def get_reserve_mode(self):
        self.configuration['Reserve mode']=int(self.read('RMOD ?'))
        
    def get_synchronous_filter(self):
        self.configuration['Synchronous filter']=int(self.read('SYNC ?'))
        
    def get_reference_source(self):
        self.configuration['Reference Source']=int(self.read('FMOD ?'))
        
    def get_phase(self):
        self.configuration['Phase']=float(self.read('PHAS ?'))
        
    def get_frequency(self):
        self.configuration['Frequency']=float(self.read('FREQ ?'))
    
    def get_reference_trigger(self):
        self.configuration['Reference trigger']=int(self.read('RSLP ?'))
    
    def get_harmonic(self):
        self.configuration['Detection harmonic']=int(self.read('HARM ?'))
    
    def get_sine_output_amplitude(self):
        self.configuration['Sine output amplitude']=float(self.read('SLVL ?'))
        
#%% Configuration of lockin functions
        
    def get_configuration(self):
        self.get_input_config()
        self.get_input_coupling()
        self.get_input_notch_filter()
        self.get_input_shield()
        self.get_synchronous_filter()
        self.get_low_pass_filter_slope()
        self.get_reserve_mode()
        self.get_sensitivity()
        self.get_time_constant()
        self.get_frequency()
        self.get_harmonic()
        self.get_phase()
        self.get_reference_source()
        self.get_reference_trigger()
        self.get_sine_output_amplitude()
    
    def set_configuration(self):
        self.set_input_config(self.configuration['Input configuration'])
        self.set_input_coupling(self.configuration['Input coupling'])
        self.set_input_notch_filter(self.configuration['Input notch filter'])
        self.set_input_shield(self.configuration['Input shield'])
        self.set_synchronous_filter(self.configuration['Synchronous filter'])
        self.set_low_pass_filter_slope(self.configuration['Low pass filter slope'])
        self.set_reserve_mode(self.configuration['Reserve mode'])
        self.set_sensitivity(self.configuration['Sensitivity'])
        self.set_time_constant(self.configuration['Time constant'])
        self.set_frequency(self.configuration['Frequency'])
        self.set_harmonic(self.configuration['Detection harmonic'])
        self.set_phase(self.configuration['Phase'])
        self.set_reference_source(self.configuration['Reference source'])
        self.set_reference_trigger(self.configuration['Reference trigger'])
        self.set_sine_output_amplitude(self.configuration['Sine output amplitude'])
        
    def saveConfiguration(self):
        pass
    
    def laodConfiguration(self):
        pass
    
#%%



if __name__ == '__main__':
    a=SR830()
    a.connect()    #a.ser.write((Command+'\r\n').encode('utf-8'))
    #a.ser.write(('++read\r\n').encode('utf-8'))
    time0=time.clock()
    for i in range(0,10):
        a.readValue('X')
        
    time1=time.clock()
    print(time1-time0)
    a.disconnect()