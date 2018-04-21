# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 18:40:06 2018

@author: t869
"""
import Stage
import Lockin

stage=Stage.Stage()
lockin=Lockin.Lockin()

for i in range(0,10):
    stage.move_relative(16)
    lockin.read_value('R')