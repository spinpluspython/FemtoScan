# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 16:08:39 2018

@author: GVolM
"""

class Instrument(object):
    def __init__(self):
        self.connection_type='COM'
        self.configuration={}
        self.load_configurution()
        
    def connect(self):
        print('unable to connect to the real instrument, function is not yet implemented')
        pass
    
    def disconnect(self):
        print('unable to disconnect from the real instrument, function is not yet implemented')
        pass
    
    def read(self):
        print('unable to read from the real instrument, function is not yet implemented')
        pass
    
    def write(self):
        print('unable to write to the real instrument, function is not yet implemented')
        pass
    
    def save_configurution(self):
        pass
    
    def load_configurution(self):
        pass
    
    def set_configurution(self):
        pass
    def get_configurution(self):
        pass