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

def sech2_fwhm(x, A, x0, fwhm,c):
    tau = fwhm*2/1.76
    return A / (np.cosh((x-x0)/tau))**2+c

def gaussian_fwhm(x, A,x0, fwhm,c):
    sig = fwhm*2/2.355
    return A*np.exp(-np.power(x - x0, 2.) / (2 * np.power(sig, 2.)))+c

def sin(x,A,f,p):
    return A* np.sin(x/f + p)

def globalcounter(idx,M):
    counterlist = idx[::-1]
    maxlist = M[::-1]
    for i in range(len(counterlist)):
        counterlist[i] = counterlist[i]*np.prod(maxlist[:i])
    return int(np.sum(counterlist))

def transient_1expdec(t, A1, tau1, sigma, y0, off):
    """ Fitting function for transients, 1 exponent decay.
    A: Amplitude
    Tau: exp decay
    sigma: pump pulse duration
    y0: whole curve offset
    off: slow dynamics offset"""
    tmp = np.erf((sigma ** 2. - 5.545 * tau1 * t) / (2.7726 * sigma * tau1))
    tmp = .5 * (1- tmp) * np.exp(sigma ** 2. / (11.09 * tau1 ** 2.))
    return y0 + tmp * (A1 * (np.exp(-t / tau1)) + off)

def main():
    pass


if __name__ == '__main__':
    main()
