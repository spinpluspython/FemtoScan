# -*- coding: utf-8 -*-
"""
Created on Wed May 29 17:19:23 2019

@author: vgrigore
"""


import thorlabs_apt as apt
apt.list_available_devices()
[(31, 27504383)]
motor = apt.Motor(27504377)
motor.move_home(True)
motor.move_by(45)