# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 18:40:06 2018

@author: t869
"""
import time
from instruments.lockinamplifier import SR830
from instruments.delaystage import DelayStage
from instruments.cryostat import Cryostat
from measurement.experiment import StepScan
from PyQt5 import QtCore, QtWidgets
import os, sys

if os.getcwd()[-9] != 'FemtoScan':
    os.chdir('../')
from utilities.misc import my_exception_hook

# used to see errors generated by PyQt5 in pycharm:
sys._excepthook = sys.excepthook
# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook

app = QtCore.QCoreApplication.instance()
if app is None:
    app = QtWidgets.QApplication(sys.argv)

time.sleep(2)
exp = StepScan()
lockin = exp.add_instrument('lockin', SR830())
stage = exp.add_instrument('delay_stage', DelayStage())
cryo = exp.add_instrument('cryo', Cryostat())
exp.print_setup()
time.sleep(1)
exp.create_file()
exp.add_parameter_iteration(cryo, 'change_temperature', [10, 20, 30, 40, 50])
exp.start_measurement()