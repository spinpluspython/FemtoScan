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
from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy
import os


extensions = [
    Extension("measurement.cscripts.project", [os.path.join("measurement", "cscripts", "project.pyx")],
        include_dirs=[numpy.get_include()]),
]

setup(
    name="FemtoScan",
    version='0.1.0',
    description='Optical Pump Probe software and instrument manager',
    author=['Steinn Ymir Agustsson','Vladimir Grigorev'],
    url='https://github.com/spinpluspython/FemtoScan',
    packages=['distutils', 'distutils.command'],
    ext_modules=cythonize(extensions)
)
