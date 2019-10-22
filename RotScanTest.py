# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 14:30:00 2019

@author: amonl
"""

from instruments import  delaystage, lockinamplifier, cryostat
import random

"""ROT SCAN"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import time
import h5py


class Rotscan_measurements(object):
    def __init__(self):
        #self.lockin_amplifier = lockinamplifier.SR830()
        self.rot_stage = delaystage.ThorLabs_rotational_stage()
        #self.cryostat = cryostat.ITC503s(COMport='COM5')
        

    def init_instruments(self):
        #self.lockin_amplifier.ser.port='COM4'
        #self.lockin_amplifier.connect()
        #self.cryostat.connect()
        ## Magnet=CurrentSupplyLib.CurrentSUP()
        ## Magnet.initcurrentsupply()
        ## Magnet.SetVoltage(40)
        ## Magnet.SetCurrent(0)
        ## Magnet.SwitchForward()
        self.rot_stage.connect()
        time.sleep(2)  # TODO: move to inside stage class
        #self.rot_stage.move_absolute(180)

    def create_points(self, N):
        Points = []
        step = 360 / N
        for i in range(0, N):
            Points.append(i * step)
        return Points
    

    @staticmethod
    def save(name, X, Y):
        File = h5py.File(name + time.ctime().replace(':','-') + ".h5", "w")
        data = np.array([X, Y])
        dset = File.create_dataset("rotscan", (len(X), 2))
        dset[...] = data.T
        File.close()
        np.savetxt(name + time.ctime().replace(':', '-') + 'txt.txt', (X,Y))

    def rotscan_measure(self, name, N_steps, save=False, time_constant=1, var='Y'):
        self.init_instruments()
        style.use("fivethirtyeight")
        fig = plt.gcf()
        fig.show()
        fig.canvas.draw()
        #time.sleep(3)        
        X = self.create_points(N_steps)
        Y = []
        
        for item in X:
            X_helper = []
            self.rot_stage.move_absolute(item)
            ##time.sleep(3*time_constant)
            Y.append(random.randint(0, N_steps))   #lockin readout herte when lockin is available!!!
            for i in range(len(Y)):
                X_helper.append([X[i]])
            
        #self.lockin_amplifier.disconnect()
            
            plt.plot(X_helper, Y)
            plt.pause(0.01)
            fig.canvas.draw()
            
        if save:
            self.save(name, X, Y) #+'-'+str(N_steps), X, Y)
        return X, Y
    

    
    
        

    def finish(self):
        #self.lockin_amplifier.disconnect()
        self.rot_stage.disconnect()
        #self.cryostat.disconnect()


# %%
def main():
    
    def turn(x):
        for i in range(2):
            meas.rot_stage.move_absolute(x+0)
            meas.rot_stage.move_absolute(x+90)
            meas.rot_stage.move_absolute(x+180)
            meas.rot_stage.move_absolute(x+270)
            
    def turnto(x):
        meas.rot_stage.move_absolute(x)

    temperature = 295.5
    save = False
    N_angles = 6
    
    meas = Rotscan_measurements()
    print(1)
    meas.init_instruments()
   
    turn(121)
    #meas.rot_stage.move_absolute(125+180)
    
    
    meas.finish()
    #or temperature in range(297,305):
     #   meas.cryostat.connect()
      #  meas.cryostat.change_temperature(temperature)
       # meas.cryostat.disconnect()
    
    """file_name = 'test'#+str(temperature)
    meas.cryostat.change_temperature(temperature)
    meas.cryostat.disconnect()
    meas.rotscan_measure(file_name, N_angles, save)  
    meas.finish()"""
    
    '''
    
    T_List = [290, 305]
    angle = 0
    
    meas = Rotscan_measurements()
    meas.init_instruments()
    #or temperature in range(297,305):
     #   meas.cryostat.connect()
      #  meas.cryostat.change_temperature(temperature)
       # meas.cryostat.disconnect()
    
    file_name = 'test'#+str(temperature)
    meas.rot_stage.move_absolute(item)
    meas.temperaturescan_measure(file_name, angle, T_List)  
    meas.finish()
    
    ''' # move these ''' right below 'def main()'
    
    
    
    
    

if __name__ == '__main__':
    main()
