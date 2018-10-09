# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 22:30:31 2018

@author: t869
"""

import Instrument
import time
class cryostat(Instrument.Instrument):
    def __init__(self):
        self.temperature_current=300
        self.temperature_set=300
    
    def connect(self):
        print('connetcted to fake cryostat. current temperature='+str(self.temperature_current)+'; setted temperature'+str(self.temperature_set))
    
    def disconnect(self):
        print('Fake cryostat has been disconnected')
        
    def get_temperature(self):
        self.temperature_current=self.temperature_current + (self.temperature_set-self.temperature_current)/2 #change current temperature closer to the setted.
        print('current temperature '+str(self.temperature_current))
        return(self.temperature_current)
    
    def set_temperature(self, temperature):
        self.temperature_set=temperature
        print('temperature is setted to'+str(temperature)+'. Wait untill real temperature become desired')
        
    
    def change_temperature(self, temperature, tolerance=0.1):
        '''set temperature to the desired Value, wait untll real temperature will become desired and stable. tolerance in kelvin'''
        self.set_temperature(temperature)
        
        self.check_temp(tolerance)
        temp=[]
        
        for i in range(1,10):
            temp.append(self.get_temperature())
            time.sleep(0.1)
        if max(temp)-min(temp)>tolerance:
            self.check_temp
        print('tamperature has reached desired value an stable. Current temperature is '+str(self.temperature_current+'K'))
            
    def check_temp(self, tolerance, sleep_time=0.1):
        while abs(self.temperature_current-self.temperature_set)>tolerance:
            time.sleep(sleep_time)
            self.get_temperature()
        
