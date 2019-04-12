# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson

    Copyright (C) 2018 Steinn Ymir Agustsson

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

# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from functools import wraps
import traceback, sys

class Exception_StopQThread(Exception):
    pass
#
#
# class Runnable(QtCore.QRunnable):
#     def __init__(self, func, args, kwargs):
#         QtCore.QRunnable.__init__(self)
#         self.func = func
#         self.args = args
#         self.kwargs = kwargs
#
#     def run(self):
#         try:
#             self.func(*self.args, **self.kwargs)
#         except Exception_StopQThread:
#             # Return using stop function
#             pass
#         except:
#             # TODO: send the exception to debug
#             pass
#
#
# pool = QtCore.QThreadPool()
# pool.setMaxThreadCount(1)  # serial execution
#

class AsQTrhead(object):

    def __init__(self, pool):
        """
        If there are decorator arguments, the function
        to be decorated is not passed to the constructor!
        """
        print("Inside __init__()")
        self.pool = pool


    def __call__(self, f):
        """
        If there are decorator arguments, __call__() is only called
        once, as part of the decoration process! You can only give
        it a single argument, which is the function object.
        """
        # print("Inside __call__()")
        def wrapped_f(*args,**kwargs):
            runnable = Runnable(func=f, args=args, kwargs=kwargs)
            self.pool.start(runnable)
        return wrapped_f

def AsQThread_(func):
    """
    Decorator to execute a func inside the QThreadPool
    """

    @wraps(func)
    def AsyncFunc(*args, **kwargs):
        runnable = Runnable(func=func, args=args, kwargs=kwargs)
        global pool
        pool.start(runnable)

    return AsyncFunc


def AsQThread__(func,pool):
    """
    Decorator to execute a func inside the QThreadPool
    """

    @wraps(func)
    def AsyncFunc(*args, **kwargs):
        runnable = Runnable(fn=func, args=args, kwargs=kwargs)
        pool.start(runnable)

    return AsyncFunc


def check_stop():
    global _STOP
    if _STOP == True:
        raise Exception_StopQThread()


def stop():
    global _STOP
    global pool
    _STOP = True
    pool.waitForDone()
    _STOP = False


class SignalCaller(QtCore.QObject):
    signal = QtCore.pyqtSignal()

    def __init__(self, func, args=(), kwargs={}):
        QtCore.QObject.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signal.connect(self.main)

    def main(self):
        self.func(*self.args, **self.kwargs)

    def run(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.signal.emit()


def GUI_Safe(func):
    """
    Decorator to execute func into the GUI thread
    """
    S = SignalCaller(func)
    return S.run


class RunnableSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    progress
        `int` indicating % progress
    """
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int)


class Runnable(QtCore.QRunnable):
    '''
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals
    and wrap-up.
    :param callback: The function callback to run on this worker
    :thread. Supplied args and
    kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    :
    '''

    def __init__(self, fn, *args, **kwargs):
        super(Runnable, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = RunnableSignals()
        # Add the callback to our kwargs
        # kwargs['progress_callback'] = self.signals.progress

    @QtCore.pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


# Test code for Ipython
# %pylab qt
# import time
# import QThreadDecorators as QTh
#
# x = arange(20)
# y = x * nan
#
# @QTh.GUI_Safe
# def myplot():
#    plot(x, y, 'bo-')
#
# @QTh.AsQThread
# def myLoop():
#    for i, xi in enumerate(x):
#        y[i] = xi**2
#        myplot()
#        time.sleep(1)
#        QTh.check_stop()
#
# myLoop()
##Wait some time...
# QTh.stop()