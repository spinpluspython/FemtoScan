# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 10:47:48 2018

@author: vgrigore
"""
from instruments import  delaystage, lockinamplifier, cryostat

"""STEP SCAN"""
import numpy as np
import matplotlib
import time
import h5py


class stepscan_measurements(object):
    def __init__(self):
        self.lockin_amplifier = lockinamplifier.SR830()
        self.delay_stage = delaystage.NewportXPS()
        #self.cryostat = cryostat.ITC503s()

    def init_instruments(self):
        #self.lockin_amplifier.connect()
        #self.cryostat.connect()
        # Magnet=CurrentSupplyLib.CurrentSUP()
        # Magnet.initcurrentsupply()
        # Magnet.SetVoltage(40)
        # Magnet.SetCurrent(0)
        # Magnet.SwitchForward()
        self.delay_stage.connect()
        time.sleep(2)  # TODO: move to inside stage class

    def create_points(self, start, stop, N):
        Points = []
        step = (stop - start) / N
        Points.append(start)
        for i in range(0, N):
            Points.append(start + i * step)
        return Points

    @staticmethod
    def save(name, X, Y):
        File = h5py.File(name + time.ctime().replace(':','-') + ".h5", "w")
        data = np.array([X, Y])
        dset = File.create_dataset("stepscan", (len(X), 2))
        dset[...] = data.T
        File.close()

    def stepscan_measure(self, name, start, stop, N):
        self.lockin_amplifier.connect()
        self.delay_stage.move_absolute(start)
        time.sleep(3)
        X = self.create_points(start, stop, N)
        Y = []
        for item in X:
            self.delay_stage.move_absolute(item)
        
            Y.append(self.lockin_amplifier.measure_avg(sleep=1))
        self.lockin_amplifier.disconnect()
        matplotlib.pyplot.plot(X, Y)
        #self.save(name + str(start) + '-' + str(stop) + '-' + str(N), X, Y)
        return X, Y

    def finish(self):
        self.lockin_amplifier.disconnect()
        self.delay_stage.disconnect()
        #self.cryostat.disconnect()


# %%
def main():

        
    meas = stepscan_measurements()
    meas.init_instruments()
    #or temperature in range(297,305):
     #   meas.cryostat.connect()
      #  meas.cryostat.change_temperature(temperature)
       # meas.cryostat.disconnect()
    file_name = 'test'#+str(temperature)
    meas.stepscan_measure(file_name, 142.58, 142.68, 100)
    meas.finish()


if __name__ == '__main__':
    main()
