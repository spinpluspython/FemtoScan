# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 12:28:55 2019

@author: amonl

Runs
"""

from instruments import  delaystage, lockinamplifier, cryostat

"""ROT SCAN"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
#import matplotlib.animation as animation
from matplotlib import style
import time
import h5py


class Rotscan_measurements(object):
    def __init__(self):
        self.lockin_amplifier = lockinamplifier.SR830_Ethernet('169.254.88.32', 1234)
        self.rot_stage = delaystage.ThorLabs_rotational_stage()
        #self.cryostat = cryostat.ITC503s()

    def init_instruments(self):
        #self.lockin_amplifier.ser.port='COM4'
        #self.lockin_amplifier.port= 1234 #'COM6'
        #self.lockin_amplifier.GPIB_adress = 8
        #self.host = "169.254.88.32"
        self.lockin_amplifier.connect()
        #self.cryostat.connect()
        self.rot_stage.connect()
        value = self.lockin_amplifier.query('++ver', 1024)
                    #'++ver\r\n')
        print(value)
        time.sleep(2)  # TODO: move to inside stage class
        
        
        
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

    def rotscan_measure(self, name, N_steps, save=False, time_constant=100, var='Y'):  #ggf. save =True
        self.init_instruments()
        #time.sleep(3)        
        X = self.create_points(N_steps)
        x_tmp =[]
        Y = []
        print("we here")
        """style.use("fivethirtyeight")
        fig = plt.gcf()
        fig.show()
        fig.canvas.draw() """
        
        
        for item in X:
            self.rot_stage.move_absolute(item)
            print("moved")
            #time.sleep(3*time_constant)
            x_tmp.append(item)
            Y.append(self.lockin_amplifier.measure_avg(sleep=1, var="Y"))
            print(Y)
            #plt.plot(x_tmp, Y)
            #plt.pause(0.01)
            #fig.canvas.draw()
        
        self.lockin_amplifier.disconnect()
        #matplotlib.pyplot.plot(X, Y)
        print(X)
        print(Y)
        if save:
            self.save(name +'-'+str(N_steps), X, Y)
        return X, Y
    
    def readLockin(self):
        print(self.lockin_amplifier.query("OUTP ? 1"))
    
    
    def temperaturescan_measure(self, name, angle, T_List, save=False, time_constant=1, var='Y'):
        self.init_instruments()
        self.rot_stage.move_absolute(angle)
        #time.sleep(3)        
        X = T_List
        Y = []
        for item in X:
            self.cryostat.change_temperature(item)
            #time.sleep(3*time_constant)
            Y.append(self.lockin_amplifier.measure_avg(sleep=time_constant, var=var))
        self.lockin_amplifier.disconnect()
        matplotlib.pyplot.plot(X, Y)
        if save:
            self.save(name +'-'+str(N_steps), X, Y)
        return X, Y
    
    def test(self):
        print(self.lockin_amplifier.measure_avg(sleep=1, var='Y'))
        
    def measureAverage(self):
        return self.lockin_amplifier.measure_avg(sleep=1, var='Y')
        
        

    def finish(self):
        self.lockin_amplifier.disconnect()
        self.rot_stage.disconnect()
        #self.cryostat.disconnect()


# %%
def main():

    
    stepnumber =8  #number of datapoints
    saveBool = True #False #True
    filename = 'test'#+str(temperature)
    
    temperature = 290
    
    data=[]
    
    Points = []
    step = 360 / stepnumber
    for i in range(0, stepnumber):
        Points.append(i * step)
    
    
    meas = Rotscan_measurements()
    meas.init_instruments()
    #meas.readLockin()
    #or temperature in range(297,305):
     #   meas.cryostat.connect()
      #  meas.cryostat.change_temperature(temperature)
       # meas.cryostat.disconnect()
    for i in Points:
        meas.rot_stage.move_absolute(i)
        data.append(meas.measureAverage())
    #meas.rot_stage.move_absolute(20)
    #meas.test()
    print(data)
    plt.plot(Points, data)
    plt.show()
    
    
    
    #for non room temp un-hashtag here    meas.cryostat.change_temperature(temperature)
    #meas.rotscan_measure(file_name, stepnumber)  
    meas.finish()
    
    
    if saveBool:
        np.savetxt("D:/RotScanTests/" + filename + '.txt', (Points, data))
    
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
