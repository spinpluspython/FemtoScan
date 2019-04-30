# -*- coding: utf-8 -*-
"""
Created on Fri Nov 24 14:51:16 2017

@author: vgrigore
"""

import CurrentSupplyLib
import lockinamplifier
import cryostat
import time
import h5py
import numpy as np
import matplotlib 

Lockin=lockinamplifier.SR830()
Lockin.connect()
cryo=cryostat.MercuryITC()
cryo.connect()
Magnet=CurrentSupplyLib.CurrentSUP()
Magnet.initcurrentsupply()
Magnet.SetVoltage(40)
Magnet.SetCurrent(0)
Magnet.SwitchForward()


def MeasureHys(filename):
    time.sleep(1)
    Magnet.SwitchForward()
    Magnet.OutputON()
    Currents=[]
    Currents2=[]
    CurrStart=0
    CurrStop=10
    step=0.5
    Signal=[]
    for i in range(0,20):
        Currents.append(CurrStart+i*step)
    for i in range(0,21):
        Currents.append(CurrStop - i*step)  
    for item in Currents:
        Currents2.append(-item)
    for item in Currents2:
        Currents.append(item)   
    
    
    for item in Currents2:
        print(-item)
        Magnet.SetCurrent(-item)
        time.sleep(3)
        Signal.append(Meas())
    Magnet.OutputOFF()
    time.sleep(1)
    Magnet.SwitchReverse()
    Magnet.OutputON()
    
    for item in Currents2:
        print(item)
        Magnet.SetCurrent(-item)
        time.sleep(3)
        Signal.append(Meas())
    Magnet.OutputOFF()
    matplotlib.pyplot.plot(Currents, Signal)
    SaveHys(filename,Currents, Signal)
        
def Meas():
    signal=[]
    avg=10
    for i in range(avg):
        signal.append(Lockin.read_value('R'))
    print(signal)
    val=sum(signal)/avg
    return val   
    
def SaveHys(name,X,Y):
    File=h5py.File(name+".hdf5", "w")
    data=np.array([X,Y])
    dset=File.create_dataset("Hys",(len(X),2))
    dset[...]=data.T
    File.close()


        
def temperature_scan():
    temperature=[4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,11,12,13,14,15,16,17,18,19,20]
    for item in temperature:
        cryo.change_temperature(item)
        filename='RuCl3-Micra-Kerr-temperature'+str(item)+str(time.time())
        MeasureHys(filename)
        
MeasureHys('test')

#temperature_scan() 
#Magnet.SetCurrent(5)
#Magnet.SwitchForward()
#Magnet.OutputON()
#time.sleep(10)
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Magnet.OutputOFF()
#Magnet.SwitchReverse()
#Magnet.OutputON()
#time.sleep(10)
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Lockin.ReadValue('R')
#Magnet.initcurrentsupply()
#Magnet.ToLocalMode()