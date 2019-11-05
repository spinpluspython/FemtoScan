# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 13:46:05 2019

@author: amonl
"""

from instruments import lockinamplifier, delaystage
import time

class Test_connection(object):
    def __init__(self):
        self.lockin_amplifier = lockinamplifier.SR830_Ethernet('169.254.88.32', 1234)
        self.rot_stage = delaystage.ThorLabs_rotational_stage()
        

    def init_instruments(self):
        print("connecting")
        self.lockin_amplifier.connect()
        self.rot_stage.connect()
        #self.lockin.port= 1234 #'COM6'
        #self.lockin.GPIB_adress = 8
        #self.host = "169.254.88.32"
        #print("connecting")
        #self.lockin.connect()
        print("connected")
        value = self.lockin_amplifier.query('++ver', 1024)
                    #'++ver\r\n')
        print(value)
        time.sleep(2)  # TODO: move to inside stage class
        
    def test(self):
        print(self.lockin_amplifier.measure_avg(sleep=1, var='Y'))
        
        
def main():
    meas = Test_connection()
    meas.init_instruments()
    meas.rot_stage.move_absolute(0)
    meas.test()
    meas.rot_stage.move_absolute(20)
    meas.test()
    meas.lockin_amplifier.close()
    print("done")
    
    
if __name__ == '__main__':
    main()
