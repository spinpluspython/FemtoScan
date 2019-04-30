# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 14:50:27 2017

@author: vgrigore
"""

import serial
import time

class CurrentSUP(object):
    '''CLass with basic methods for current supply'''
    def __init__(self):
        self.COMport='COM4'  #Comport wich current suply is connected to
        self.COMportSwitch='COM3' # COMport of the switch
        self.RSaddress='A007'    #address of RS-485 port(manually go to menu on the Supply and change address)
        self.Current=0 #Seted Current
        self.Voltage=0 # seted Voltage
        self.VoltageMeas=0 # measured voltage
        self.CurrentMeas=0 #measured current
        self.CurrentON=True #current status
        
    def writestring(self, SCPICommands):
        '''Transform list of SCPI commands to strig for writing to RS-485 port. Adds address of port and seporator, transform it to required format. SCPICommands should be list of strings'''
        String=''
        for item in SCPICommands:
            String=String+self.RSaddress + item + ';'
        return String.encode('utf-8')
        
    def writeSCPICommand(self, SCPICommand):
        '''writes string of SCPI commands to RS port. init port and configure it'''
        ser=serial.Serial()
        ser.baudrate=115200
        ser.port=self.COMport
        try:
            ser.open()
            ser.write(self.writestring(SCPICommand))
            ser.close()
        except: ser.close()
        
    def initcurrentsupply(self):
        '''Init current supply, switch it to remote mode, set 0 current and 0 voltage, output off'''
        SCPICommands=['SYST:REM', 'SOUR:VOLT 40.0', 'SOUR:CURR 10.0', 'OUTP 1','SOUR:VOLT 0.0', 'SOUR:CURR 0.0', 'OUTP 0']
        self.CurrentON=False
        #print(self.writestring(SCPICommands))
        self.writeSCPICommand(SCPICommands)
    
    def SetCurrent(self, Current):
        '''Sets current on the current supply, doesn't switch on output'''
        self.Current=Current
        SCPICommands=['SYST:REM', 'SOUR:CURR '+str(self.Current)]
        self.writeSCPICommand(SCPICommands)
        
    def SetVoltage(self, Voltage):
        '''Sets voltage in Volts on the current supply, doesn't switch on output'''
        self.Voltage=Voltage
        SCPICommands=['SYST:REM', 'SOUR:VOLT '+str(self.Voltage)]
        self.writeSCPICommand(SCPICommands)
    
    def OutputON(self):
        '''Put setted current on the current supply'''
        SCPICommands=['SYST:REM', 'OUTP 1']
        self.writeSCPICommand(SCPICommands)
        time.sleep(0.3)
        self.CurrentON=True
        print( 'Current is put on magnet!!!')
    
    def OutputOFF(self):
        '''switchs off current'''
        SCPICommands=['SYST:REM', 'OUTP 0']
        self.writeSCPICommand(SCPICommands)
        self.CurrentON=False
        print('Output OFF')
        
    def ToLocalMode(self):
        '''switch current cupply to local mode with 0 current and voltage'''
        SCPICommands=['SYST:REM','SOUR:VOLT 0.0', 'SOUR:CURR 0.0', 'OUTP 0', 'SYST:LOC']
        self.writeSCPICommand(SCPICommands)
        
    def GetVoltage(self):
        '''measures actual voltage on the current supply and return it in Volts, write it self.VoltageMeas'''
        ser=serial.Serial()
        ser.baudrate=115200
        ser.port=self.COMport
        try:
            ser.open()
            ser.write(self.writestring(['MEAS:VOLT?']))
            Value=float(str(ser.readline())[2:13])
            ser.close()
            self.VoltageMeas=Value
            return Value
        except: ser.close()
        
    
    def GetCurrent(self):
        '''measures actual current on the current supply and return it in Amps, write it self.CurrentMeas'''
        ser=serial.Serial()
        ser.baudrate=115200
        ser.port=self.COMport
        try:
            ser.open()
            ser.write(self.writestring(['MEAS:CURR?']))
            Value=float(str(ser.readline())[2:13])
            ser.close()
            self.CurrentMeas=Value
            return Value
        except: ser.close()
        
    def ReadAddress(self):
        '''return address of RS port'''
        ser=serial.Serial()
        ser.baudrate=115200
        ser.port=self.COMport
        try:
            ser.open()
            ser.write(self.writestring(['MEAS:ADDR?']))
            Value=ser.readline()
            ser.close()
            return Value
        except: ser.close()
    
    def SwitchReverse(self):
        '''switch current to revers'''
        ser=serial.Serial()
        ser.baudrate=9600
        ser.port=self.COMportSwitch
        try:
            ser.open()
            time.sleep(1)
            ser.write('Reverse'.encode('utf-8'))
            ser.close()
        except: 
            ser.close()
            print('error')
        
     
    def SwitchForward(self):
        '''switch current to forward'''
        if self.CurrentON:  #check if current is off
            self.OutputOFF() # switch it off
        ser=serial.Serial()
        ser.baudrate=9600
        ser.port=self.COMportSwitch
        try:
            ser.open()
            time.sleep(1)
            ser.write('Forward'.encode('utf-8'))
            ser.close()
        except: 
            ser.close()
            print('error')
            
if __name__=='__main__':
    ser=serial.Serial()
    ser.baudrate=9600
    ser.port='COM3'
    ser.open()
    time.sleep(1)
    ser.write('Reverse'.encode('utf-8'))
    ser.close() 