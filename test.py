# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 18:40:06 2018

@author: t869
"""
from instruments.lockinamplifier import LockInAmplifier
from instruments.delaystage import DelayStage
from measurement.core import Experiment

exp=Experiment()
exp.add_instrument('lockin',LockInAmplifier())
exp.add_instrument('stage',DelayStage())
import time
time.sleep(2)
exp.measure([exp.lockin.read_value('R'),exp.lockin.read_value('T')],[exp.stage.move_absolute],[[0,1,2,3,4,5,6,7,8,9,10]])
