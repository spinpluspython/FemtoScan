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

import nidaqmx
import numpy as np
from PyQt5 import QtCore
from nidaqmx import stream_readers
from nidaqmx.constants import Edge, AcquisitionType

from utilities.math import gaussian_fwhm, gaussian, sech2_fwhm, transient_1expdec
from utilities.settings import parse_setting


def main():
    pass


if __name__ == '__main__':
    main()


class FastScanStreamer(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(np.ndarray)
    error = QtCore.pyqtSignal(Exception)

    def __init__(self, n_samples, iterations=None, simulate=False, dark_control=True):
        super().__init__()
        self.logger = logging.getLogger('{}.FastScanStreamer'.format(__name__))
        self.logger.info('Created FastScanStreamer')

        self.n_samples = n_samples
        self.iterations = iterations
        self.data = np.zeros((3, n_samples))
        self.simulate = simulate
        self.dark_control = dark_control
        self.should_stop = True

    @QtCore.pyqtSlot()
    def start_acquisition(self):
        if self.simulate:
            self.logger.info('Started streamer simulation')
            self.start_simulated_acquisition()
        else:
            try:
                self.logger.info('Started NI FastScanStreamer')
                with nidaqmx.Task() as task:

                    self.reader = stream_readers.AnalogMultiChannelReader(task.in_stream)
                    self.logger.debug('reader initialized')
                    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")  # shaker position chanel
                    task.ai_channels.add_ai_voltage_chan("Dev1/ai1")  # signal chanel
                    task.ai_channels.add_ai_voltage_chan("Dev1/ai2")  # dark control chanel
                    self.logger.debug('added 3 tasks')
                    task.timing.cfg_samp_clk_timing(1000000, source="/Dev1/PFI0",
                                                    active_edge=Edge.RISING,
                                                    sample_mode=AcquisitionType.CONTINUOUS)
                    task.start()
                    self.logger.info('FastScanStreamer taks started')

                    self.should_stop = False
                    i = 0
                    while True:
                        i += 1
                        self.logger.debug('measuring cycle {}'.format(i))
                        self.measure()
                        if self.iterations is not None and i >= self.iterations:
                            self.should_stop = True
                        if self.should_stop:
                            self.logger.warning('Acquisition stopped.')
                            self.finished.emit()
                            break

            except Exception as e:
                self.logger.warning('Error while starting streamer: \n{}'.format(e))
                self.error.emit(e)

    @QtCore.pyqtSlot()
    def stop_acquisition(self):
        self.logger.info('FastScanStreamer thread stopping.')
        self.should_stop = True

    def measure(self):
        self.reader.read_many_sample(self.data, number_of_samples_per_channel=self.n_samples)
        self.logger.debug('Recieved data from NI card: mean axis 0 = {}'.format(self.data[0].mean()))
        self.newData.emit(self.data)

    def start_simulated_acquisition(self):
        self.should_stop = False

        if self.iterations is None:
            i = 0
            while not self.should_stop:
                i += 1
                self.logger.debug('simulating measurement cycle #{}'.format(i))
                self.simulate_measure()
        else:
            for i in range(self.iterations):
                self.logger.debug('simulating measurement cycle #{} of {}'.format(i, self.iterations))
                self.simulate_measure()

    def simulate_measure(self, function='sech2_fwhm', args=[.5, -2, .085, 1], amplitude=10):
        data = self.data
        t0 = time.time()
        args_ = args[:]
        step = parse_setting('fastscan', 'shaker_position_step')
        ps_per_step =  parse_setting('fastscan','shaker_ps_per_step')# ADC step size - corresponds to 25fs

        if function == 'gauss_fwhm':
            f = gaussian_fwhm
            args_[1] *= step/ps_per_step  # transform ps to voltage
            args_[2] *= step/ps_per_step  # transform ps to voltage
        elif function == 'gaussian':
            f = gaussian
            step = parse_setting('fastscan','shaker_position_step')
            args_[1] *= step/ps_per_step  # transform ps to voltage
            args_[2] *= step/ps_per_step  # transform ps to voltage
            args_.pop(0)
            args_.pop(-1)
        elif function == 'sech2_fwhm':
            f = sech2_fwhm
            step = parse_setting('fastscan','shaker_position_step')
            args_[1] *= step/ps_per_step  # transform ps to voltage
            args_[2] *= step/ps_per_step  # transform ps to voltage
        elif function == 'transient_1expdec':
            f = transient_1expdec
            step = parse_setting('fastscan','shaker_position_step')

            args_ = [2, 20, 1, 1, .01, -10]
            args_[1] *= step/ps_per_step  # transform ps to voltage
            args_[2] *= step/ps_per_step  # transform ps to voltage
            args_[5] *= step/ps_per_step  # transform ps to voltage

        else:
            raise NotImplementedError('no funcion called {}, please use gauss or sech2'.format(function))
        #########
        n = np.arange(len(data[0]))
        noise = np.random.rand(len(n))
        phase = noise[0] * 2 * np.pi

        amplitude = amplitude * step/ps_per_step * (1 + .02 * np.random.uniform(-1, 1))


        data[0, :] = np.cos(2 * np.pi * n / 30000 + phase) * amplitude / 2  # in volt

        data[1, 1::2] = data[0, 1::2] / 3
        data[1, ::2] = f(data[0, ::2], *args_) + noise[::2] + data[0, ::2] / 3
        data[2, ::2] = True
        data[2, 1::2] = False
        ####
        dt = time.time() - t0

        # QtCore.QTimer.singleShot(max(self.n_samples / 273000 - dt, 0),self.emit_data)
        time.sleep(max(self.n_samples / 273000 - dt, 0))
        self.logger.debug(
            'simulated data in {:.2f} ms - real would take {:.2f} - '
            'outputting array of {}'.format(dt * 1000, self.n_samples / 273, self.data.shape))

        self.newData.emit(self.data)
    def emit_data(self):
        self.newData.emit(self.data)
