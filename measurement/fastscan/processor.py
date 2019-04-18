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
import logging
import time

import numpy as np
import xarray as xr
from PyQt5 import QtCore
from scipy.optimize import curve_fit

from utilities.math import sech2_fwhm, sin
from utilities.settings import parse_setting


class FastScanProcessor(QtCore.QObject):
    isReady = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(xr.DataArray)
    newFit = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(Exception)

    def __init__(self, id):
        super().__init__()
        self.logger = logging.getLogger('{}.FastScanProcessor'.format(__name__))
        self.logger.debug('Created FastScanProcessor: id={}'.format(id))
        self.id = id

    def initialize(self):
        self.isReady.emit(self.id)

    @QtCore.pyqtSlot()
    def project(self, stream_data, use_dark_control=True):
        """ project data from streamer format to 1d time trace

        creates bins from digitizing the stage positions measured channel of the
        stream data. Values from the signal channel are assigned to the corresponding
        bin from the stage positions. if Dark Control is true, values where dc
        is true are added, while where dark control is false, it is substracted.

        :param stream_data:
        :param use_dark_control:
        :return:
            xarray containing projected data and relative time scale.

        """
        time.sleep(5)
        self.logger.debug('Processor ID:{} started processing data with shape {}'.format(self.id, stream_data.shape))
        t0 = time.time()
        adc_step = parse_setting('fastscan', 'shaker_position_step')
        ps_per_step = parse_setting('fastscan', 'shaker_ps_per_step')  # ADC step size - corresponds to 25fs
        ps_per_step *= parse_setting('fastscan', 'shaker_gain')  # correct for shaker gain factor

        try:
            result = project(stream_data, use_dark_control=use_dark_control,
                             adc_step=adc_step, time_step=ps_per_step)
            self.newData.emit(result)

            self.logger.debug('Projected {} points to a {} pts array, with {} nans in : {:.2f} ms'.format(
                stream_data.shape[1], result.shape,
                len(result) - len(result[np.isfinite(result)]),
                1000 * (time.time() - t0)))

        except Exception as e:
            self.logger.warning(
                'failed to project stream_data.\nERROR: {}'.format(e))
            self.error.emit(e)

        time.sleep(0.002)
        self.isReady.emit(self.id)
        self.logger.debug('Processor ID:{} is ready for new stream_data'.format(self.id))

    @QtCore.pyqtSlot()
    def fit_sech2(self, da):

        try:
            fitDict = fit_autocorrelation(da)
            self.newFit.emit(fitDict)
        except RuntimeError as e:
            self.logger.critical('Fitting failed: Runtime error: {}'.format(e))
        except Exception as e:
            self.logger.critical('Fitting failed: {}'.format(e))


def fit_autocorrelation(da, expected_pulse_duration=.1):
    """ fits the given data to a sech2 pulse shape"""
    da_ = da.dropna('time')

    xc = da_.time[np.argmax(da_.values)]
    off = da_[da_.time - xc > .2].mean()
    a = da_.max() - off

    guess = [a, xc, expected_pulse_duration, off]
    try:
        popt, pcov = curve_fit(sech2_fwhm, da_.time, da_, p0=guess)
    except RuntimeError:
        popt, pcov = [0, 0, 0, 0], np.zeros((4, 4))
    fitDict = {'popt': popt,
               'pcov': pcov,
               'perr': np.sqrt(np.diag(pcov)),
               'curve': xr.DataArray(sech2_fwhm(da_.time, *popt), coords={'time': da_.time}, dims='time')
               }
    return fitDict


def project(stream_data, use_dark_control=True, adc_step=0.000152587890625, time_step=.05):
    spos_analog = stream_data[0]
    x = np.arange(0, len(spos_analog), 1)

    g_amp = spos_analog.max() - spos_analog.min()
    g_freq = 15000 / np.pi
    g_phase = 0
    g_offset = g_amp / 5
    guess = [g_amp, g_freq, g_phase, g_offset]
    popt, pcov = curve_fit(sin, x, spos_analog, p0=guess)
    spos = sin(x, *popt)

    spos = np.array(spos / adc_step, dtype=int)
    spos_range = (spos.min(), spos.max())
    signal = stream_data[1]
    dark_control = stream_data[2]

    result = np.zeros(spos_range[1] - spos_range[0] + 1)
    norm_array = np.zeros(spos_range[1] - spos_range[0] + 1)

    if use_dark_control:
        for val, pos, dc in zip(signal, spos - spos_range[0], dark_control):
            if dc:
                result[pos] += val
                norm_array[pos] += 1.
            else:
                result[pos] -= val
    else:
        for val, pos in zip(signal, spos - spos_range[0]):
            result[pos] += val
            norm_array[pos] += 1.

    result /= norm_array
    time_axis = np.arange(spos_range[0], spos_range[1] + 1, 1) * time_step
    return xr.DataArray(result, coords={'time': time_axis}, dims='time').dropna('time')


if __name__ == '__main__':
    from measurement.fastscan.streamer import simulate_measure
    import matplotlib.pyplot as plt

    sim = simulate_measure(np.zeros([3, 42000]), args=[1, 0, .085, .1], amplitude=10)
    plt.plot(sim[0])
    plt.show()
    res = project(sim, use_dark_control=True)  # ,fitpar=(.025, np.pi / (15000), -1, .005))

    print(res)
