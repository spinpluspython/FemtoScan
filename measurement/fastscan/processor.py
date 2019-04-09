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

from utilities.settings import parse_setting
from utilities.math import gaussian_fwhm, gaussian, sech2_fwhm, transient_1expdec


def main():
    pass


if __name__ == '__main__':
    main()


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
    def project(self, stream_data, use_dark_control=True, smooth='fit', guess=(.025, np.pi / (15000), -1, .005)):
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

        step = parse_setting('fastscan','shaker_position_step')
        ps_per_step =  parse_setting('fastscan','shaker_ps_per_step')# ADC step size - corresponds to 25fs
        # consider 0.1 ps step size from shaker digitalized signal,

        # step_to_time_factor = .05  # should be considering the 2 passes through the shaker
        minpos = shaker_positions.min()
        min_t = (minpos / step) * ps_per_step
        maxpos = shaker_positions.max()
        max_t = (maxpos / step) * ps_per_step

        n_points = int((maxpos - minpos) / step) + 1
        time_axis = np.linspace(min_t, max_t, n_points)

        position_bins = np.array((shaker_positions - minpos) / step, dtype=int)

        try:
            if use_dark_control:
                result = np.zeros(n_points, dtype=np.float64)
                norm_array = np.zeros(n_points, dtype=np.float64)
                for val, pos, dc in zip(signal, position_bins, dark_control):
                    if dc:
                        result[pos] += val
                        norm_array[pos] += 1.
                    else:
                        result[pos] -= val

                result /= norm_array
            else:
                result = np.zeros(n_points, dtype=np.float64)
                norm_array = np.zeros(n_points, dtype=np.float64)
                for val, pos in zip(signal, position_bins):
                    result[pos] += val
                    norm_array[pos] += 1.
                result /= norm_array

            output = xr.DataArray(result, coords={'time': time_axis}, dims='time')

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

    def fit_sech2(self,da):

        f = sech2_fwhm


        # guess = [1, 0, .1, 0]
        xc = da.time[np.argmax(da.values)]
        off = da[da.time - xc > .2].mean()
        a = da.max() - off
        guess = [a,xc,.1,off]
        try:
            popt,pcov = curve_fit(f,da.time,da,p0=guess)
            fitDict = {'popt':popt,
                       'pcov':pcov,
                       'perr':np.sqrt(np.diag(pcov)),
                       'curve':xr.DataArray(f(da.time,*popt), coords={'time': da.time}, dims='time')
                       }

            self.newFit.emit(fitDict)


        except Exception as e:
            self.logger.critical('Fitting failed: {}'.format(e))


