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
from scipy.signal import butter, filtfilt

from utilities.math import sech2_fwhm, sin
from utilities.settings import parse_setting


class FastScanProcessor(QtCore.QObject):
    isReady = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(xr.DataArray)
    newFit = QtCore.pyqtSignal(dict)
    # newDatadict = QtCore.pyqtSignal(dict)
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

        self.logger.debug('Processor ID:{} started processing data with shape {}'.format(self.id, stream_data.shape))
        t0 = time.time()
        try:
            result = project(stream_data, use_dark_control=use_dark_control)
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
    def project_old(self, stream_data, use_dark_control=True, smooth='fit', guess=(.025, np.pi / (15000), -1, .005)):
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

        self.logger.debug('Processor ID:{} started processing data with shape {}'.format(self.id, stream_data.shape))
        t0 = time.time()
        shaker_positions = stream_data[0]
        signal = stream_data[1]
        dark_control = stream_data[2]

        if smooth == 'fit':
            def sin(t, a, freq, phase, offset):
                return a * np.sin(t * freq + phase) + offset

            x = np.linspace(0, len(shaker_positions) - 1, len(shaker_positions))
            popt, pcov = curve_fit(sin, x, shaker_positions, p0=guess)
            shaker_positions = sin(x, *popt)
        elif smooth == 'filter':

            b, a = butter(2, .001)
            shaker_positions = filtfilt(b, a, shaker_positions)

        step = parse_setting('fastscan', 'shaker_position_step')
        ps_per_step = parse_setting('fastscan', 'shaker_ps_per_step')  # ADC step size - corresponds to 25fs
        # consider 0.05 ps step size from shaker digitalized signal,

        # step_to_time_factor = .05  # should be considering the 2 passes through the shaker
        minpos = shaker_positions.min()
        min_t = (minpos / step) * ps_per_step
        maxpos = shaker_positions.max()
        max_t = (maxpos / step) * ps_per_step

        position_bins = np.array((shaker_positions - minpos) / step, dtype=int)
        time_axis, time_bins = make_time_bins(min_t, max_t, ps_per_step)

        result = np.zeros_like(time_axis)
        norm_array = np.zeros_like(time_axis)

        try:
            if use_dark_control:
                for val, pos, dc in zip(signal, position_bins, dark_control):
                    if dc:
                        result[pos] += val
                        norm_array[pos] += 1.
                    else:
                        result[pos] -= val
                result /= norm_array
            else:

                for val, pos in zip(signal, position_bins):
                    result[pos] += val
                    norm_array[pos] += 1.
                result /= norm_array

            res = xr.DataArray(result, coords={'time': time_axis}, dims='time')
            output = xr.DataArray(res.groupby_bins('time', time_bins).mean(),
                                  coords={'time': time_axis}, dims='time').dropna('time')
            self.newData.emit(output)

            self.logger.debug('Projected {} points to a {} pts array, with {} nans in : {:.2f} ms'.format(
                len(signal), len(result),
                len(result) - len(result[np.isfinite(result)]),
                1000 * (time.time() - t0)))

        except Exception as e:
            self.logger.warning(
                'failed to project stream_data with shape {} to shape {}.\nERROR: {}'.format(shaker_positions.shape,
                                                                                             output.shape, e))
            self.error.emit(e)

        time.sleep(0.002)
        self.isReady.emit(self.id)
        self.logger.debug('Processor ID:{} is ready for new stream_data'.format(self.id))

    @QtCore.pyqtSlot(dict, xr.DataArray)
    def calc_avg(self, data_dict, processor_data):
        try:
            data_dict['all'] = xr.concat([data_dict['all'], processor_data], 'avg')
            if 'avg' in data_dict['all'].dims:
                data_dict['average'] = data_dict['all'][-100:].mean('avg')
        except KeyError:
            data_dict['all'] = processor_data
        self.newDatadict.emit(data_dict)

    def fit_sech2(self, da):

        da_ = da.dropna('time')
        # guess = [1, 0, .1, 0]
        xc = da_.time[np.argmax(da_.values)]
        off = da_[da_.time - xc > .2].mean()
        a = da_.max() - off
        guess = [a, xc, .1, off]
        try:
            popt, pcov = curve_fit(sech2_fwhm, da_.time, da_, p0=guess)
            fitDict = {'popt': popt,
                       'pcov': pcov,
                       'perr': np.sqrt(np.diag(pcov)),
                       'curve': xr.DataArray(sech2_fwhm(da_.time, *popt), coords={'time': da_.time}, dims='time')
                       }
            self.logger.debug('Fitting successful')

            self.newFit.emit(fitDict)


        except Exception as e:
            self.logger.critical('Fitting failed: {}'.format(e))


def make_time_bins(min_t, max_t, step):
    bins = np.arange(step * np.floor(min_t / step) - step / 2, step * np.ceil(max_t / step) + step / 2, step)
    axis = bins[:-1] + step / 2
    return axis, bins


def project(stream_data, use_dark_control=True):
    adc_step = 0.000152587890625
    time_step = .05  # ps

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
