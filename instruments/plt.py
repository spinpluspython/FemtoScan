# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 20:09:57 2018

@author: vgrigore
"""

import matplotlib.pyplot as plt
import os
import h5py
import numpy as np

class scan(object):
    def __init__(self):
       self.X=[]
       self.Y=[]
       self.Y1=[]
       self.temperature=0
    
    def import_file(self,filename):
        file=h5py.File(filename)
        d=np.array(file['Hys'])
        self.X=d.T[0]
        self.Y=d.T[1]
        self.Y1=self.Y - self.Y[10]
        #self.temperature=float(filename[20:22])
        
    def plot(self,offset=0):
        fig, ax=plt.subplots()
        Y1=self.Y1+offset
        ax.plot(self.X,Y1, label='temp='+str(self.temperature)+' k')
        leg = ax.legend()
#%%
class scans(object):
    def __init__(self):
        self.scans=[]
        self.filenames=[]
    
    def import_all(self):
        files=os.listdir()
        for item in files:
            if item[0:3]=='RuC':
                self.filenames.append(item)
        for item in self.filenames:
            sc=scan()
            sc.import_file(item)
            self.scans.append(sc)
            

            
    def plot_all(self):
        fig,ax=plt.subplots()
        for i,item in enumerate(self.scans):
            
            ax.plot(item.X,item.Y1+item.temperature*0.0001,label='temp='+str(item.temperature)+' k')
            
        ax.legend()


#%%        
def plot_one(filename,offset=0):
    #filename='BNA-pu-0.75-pr-0.2-4-87.5--80-420Mon Oct 22 19-39-25 2018.h5'
    file=h5py.File(filename)
    d=np.array(file['stepscan'])
    X=d.T[0]
    X_time=X
    Y=d.T[1]
    Y1=Y-Y[5]+offset
    temperature=float(filename[20:22])
    fig, ax=plt.subplots()
    ax.plot(X_time,Y1,lebal='temp='+str(temperature)+' k')
    leg=ax.legend()
    
def plot_all():
    files=os.listdir()
    filenames=[]
    for item in files:
        if item[0:3]=='BNA':
            filenames.append(item)
    
    for i, item in enumerate(filenames):
        plot_one(item,offset=i*0.00008)


def fit_one(filename):
    file=h5py.File(filename)
    d=np.array(file['stepscan'])
    X=d.T[0]
    X_time=X*2/0.3 + 578
    Y=d.T[1]
    Y1=Y-Y[5]
    
    
 
scs=scans()
scs.import_all()
scs.plot_all()
#plot_all()    
#filename='BNA-pu-0.75-pr-0.2-4-87.5--80-420Mon Oct 22 19-39-25 2018.h5'   
#plot_one('BNA-pu-0.75-pr-0.2-T-10-[(-87.2, -86, 300), (-86, -80, 100), (-80, -50, 20)]Thu Oct 25 01-41-55 2018.h5')