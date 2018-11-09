# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson

    Copyright (C) 2018 Steinn Ymir Agustsson, Vladimir Grigorev

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import sys, os
import time
from PyQt5 import QtWidgets, QtCore

from utilities.settings import parse_setting
if not os.path.isfile('SETTINGS.ini'):
    from utilities.settings import make_settings, parse_setting

    make_settings()

_MODE = parse_setting('launcher', 'mode')
""" 'cmd' to run command line execution, 'gui' to start the graphical interface"""
_RECOMPILE = parse_setting('launcher', 'recompile')



def launch_cmd():
    from measurement.stepscan import StepScan
    from instruments.lockinamplifier import SR830, LockInAmplifier
    from instruments.delaystage import DelayStage
    from instruments.cryostat import Cryostat

    time.sleep(2)
    exp = StepScan()
    lockin = exp.add_instrument('lockin', LockInAmplifier())
    stage = exp.add_instrument('delay_stage', DelayStage())
    cryo = exp.add_instrument('cryo', Cryostat())
    exp.print_setup()
    time.sleep(1)
    exp.add_parameter_iteration('temperature','K',cryo, 'change_temperature', [10,20])
    # exp.set_name =  'somename'

    exp.create_file()
    exp.start_measurement()

def launch_gui():


    from gui.mainwindow import MainWindow
    from utilities.qt import my_exception_hook, recompile
    # used to see errors generated by PyQt5 in pycharm:
    sys._excepthook = sys.excepthook
    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook

    if _RECOMPILE:
        recompile('the/right/folder/whit/ui_stuff.ui')

    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    # Create handle prg for the Graphic Interface
    prg = MainWindow()

    print('showing GUI')
    prg.show()



if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    if _MODE == 'cmd':
        launch_cmd()
    elif _MODE == 'gui':
        launch_gui()
    else:
        print('unrecognized mode {}'.format(_MODE))

    try:
        app.exec_()
    except:
        print('app.exec_() failed: exiting')