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
import numpy as np


def monotonically_increasing(l):
    return all(x < y for x, y in zip(l, l[1:]))


def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

def sin(x,A,f,p):
    return A* np.sin(x/f + p)

def globalcounter(idx,M):
    counterlist = idx[::-1]
    maxlist = M[::-1]
    for i in range(len(counterlist)):
        counterlist[i] = counterlist[i]*np.prod(maxlist[:i])
    return int(np.sum(counterlist))


def main():
    pass


if __name__ == '__main__':
    main()
