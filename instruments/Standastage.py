# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 20:04:53 2019

@author: vgrigore
"""

import ctypes
mydll=ctypes.cdll.LoadLibrary('USMCDLL.dll')

class USMC_Devices(ctypes.Structure):
    """Wrapper class for USMC_Devices structure.
    
    Attributes
    ----------
    NOD : int
        Number of stepper motor controllers (axes).
    Serial : list of strings
        List containing the serial numbers of all controllers.
    Version : list of string
        List containing the version number of all controllers.
    
    """
    _fields_ = [
        ("NOD", ctypes.wintypes.DWORD),
        ("Serial", ctypes.POINTER(ctypes.c_char_p)),
        ("Version", ctypes.POINTER(ctypes.c_char_p)),
        ]

a=USMC_Devices()
mydll.USMC_Init(a)
print(a.NOD)