# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 10:47:48 2018

@author: vgrigore
"""

"""STEP SCAN"""
import numpy as np
import matplotlib
import SR830_Lockin
import NewPortStage
import mercury_ITC
import time
import h5py

class stepscan_measurements(object):
    def __init__(self):
        self.Lockin=SR830_Lockin.SR830()
        self.Stage=NewPortStage.NewPortStage()
        self.Cryostat=mercury_ITC.mercury_ITC()
        
       

    def init_instruments(self):
        self.Lockin.connect()
        self.Cryostat.connect()
        #Magnet=CurrentSupplyLib.CurrentSUP()
        #Magnet.initcurrentsupply()
        #Magnet.SetVoltage(40)
        #Magnet.SetCurrent(0)
        #Magnet.SwitchForward()
        self.Stage.connect()
        time.sleep(2)


    def create_points(self, start, stop, N):
        Points=[]
        step=(stop-start)/N
        Points.append(start)
        for i in range(0,N):
            Points.append(start+i*step)
        return Points
    

    def save(name,X,Y):
        File=h5py.File(name+".hdf5", "w")
        data=np.array([X,Y])
        dset=File.create_dataset("stepscan",(len(X),2))
        dset[...]=data.T        
        File.close()

    def stepscan_measure(self, name, start, stop, N):
        self.Stage.move_absolute(start)
        time.sleep(3)
        X=self.create_points(start,stop,N)
        Y=[]
        for item in X:
            self.Stage.move_absolute(item)
            #time.sleep(0.0)
            Y.append(self.Lockin.read_value('R'))
            matplotlib.pyplot.plot(X,Y)
            self.save(name+str(start)+'-'+str(stop)+'-'+str(N),X,Y)
        return X,Y
    
    def finish(self):
        self.Lockin.disconnect()
        self.Stage.disconnect()
        self.Cryostat.disconnect()
#%%
def main():
    meas=stepscan_measurements()
    meas.init_instruments()
    file_name='test'
    meas.stepscan_measure(file_name,-100,0,10)
    
if __name__=='__main__':
    main()