# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 18:40:06 2018

@author: t869
"""
from instruments import delaystage, lockinamplifier

stage= delaystage.DelayStage()
lockin= lockinamplifier.LockInAmplifier()
stage.connect()
lockin.connect()
for i in range(0,10):
    stage.move_relative(16)
    lockin.read_value('R')
    
stage.set_zero_position()
stage.move_relative(-10)
lockin.disconnect()
stage.disconnect()