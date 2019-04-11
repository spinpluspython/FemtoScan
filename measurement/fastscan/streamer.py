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
from PyQt5 import QtCore
try:
    import nidaqmx
    from nidaqmx import stream_readers
    from nidaqmx.constants import Edge, AcquisitionType
except:
    print('no nidaqmx package found, only simulations available')
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

    def __init__(self, n_samples, iterations=None, dark_control=True, simulate=False):
        super().__init__()
        self.logger = logging.getLogger('{}.FastScanStreamer'.format(__name__))
        self.logger.info('Created FastScanStreamer')

        self.n_samples = n_samples
        self.iterations = iterations
        self.data = np.zeros((3, n_samples))
        self.acquisition_mode = parse_setting('fastscan','acquisition_mode')
        self.simulate = parse_setting('fastscan','simulate') #todo: remove reference for simulation from everywhere else
        self.dark_control = dark_control
        self.should_stop = True

        self.sim_clock = QtCore.QTimer()
        self.sim_clock.setInterval(n_samples / 273000)
        self.sim_clock.timeout.connect(self.on_sim_clock)
        # self.sim_clock.start()

    @QtCore.pyqtSlot()
    def start_acquisition(self):
        if self.simulate:
            self.logger.info('Started streamer simulation in {} mode'.format(self.acquisition_mode))
            self.measure_simulated()
        else:
            if self.acquisition_mode == 'continuous':
                self.logger.info('Started NI continuous Streamer ')
                self.measure_continuous()

            elif self.acquisition_mode == 'triggered':
                self.logger.info('Started NI triggered Streamer ')
                self.measure_triggered()

    @QtCore.pyqtSlot()
    def stop_acquisition(self):
        self.logger.info('FastScanStreamer thread stopping.')
        self.should_stop = True

    def measure_continuous(self):
        try:
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
                    self.reader.read_many_sample(self.data, number_of_samples_per_channel=self.n_samples)
                    self.logger.debug('Recieved data from NI card: mean axis 0 = {}'.format(self.data[0].mean()))
                    self.newData.emit(self.data)
                    if self.iterations is not None and i >= self.iterations:
                        self.should_stop = True
                    if self.should_stop:
                        self.logger.warning('Acquisition stopped.')
                        self.finished.emit()
                        break

        except Exception as e:
            self.logger.warning('Error while starting streamer: \n{}'.format(e))
            self.error.emit(e)

    def measure_triggered(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")  # shaker position chanel
            task.ai_channels.add_ai_voltage_chan("Dev1/ai1")  # signal chanel
            task.ai_channels.add_ai_voltage_chan("Dev1/ai2")  # dark control chanel

            task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source="/Dev1/PFI1",
                                                                trigger_edge=Edge.RISING)
            task.timing.cfg_samp_clk_timing(100000, samps_per_chan=self.n_samples,
                                            source="/Dev1/PFI0",
                                            active_edge=Edge.RISING,
                                            sample_mode=AcquisitionType.FINITE)  # external clock chanel

            self.should_stop = False
            i = 0
            while True:
                i += 1
                self.logger.debug('measuring cycle {}'.format(i))
                self.data = np.array(task.read(number_of_samples_per_channel=self.n_samples))

                self.newData.emit(self.data)

                if self.iterations is not None and i >= self.iterations:
                    self.should_stop = True
                if self.should_stop:
                    self.logger.warning('Acquisition stopped.')
                    self.finished.emit()
                    break

    def measure_simulated(self):
        self.should_stop = False

        if self.iterations is None:
            i = 0
            while not self.should_stop:
                i += 1
                self.logger.debug('simulating measurement cycle #{}'.format(i))
                t0 = time.time()

                self.data = simulate_measure(self.data,
                                             function='sech2_fwhm',
                                             args=[.5, -2, .085, 1],
                                             amplitude=50,
                                             mode=self.acquisition_mode)
                dt = time.time() - t0
                time.sleep(max(self.n_samples / 273000 - dt, 0))
                self.newData.emit(self.data)

                self.newData.emit(self.data)
                self.logger.debug(
                    'simulated data in {:.2f} ms - real would take {:.2f} - '
                    'outputting array of shape {}'.format(dt * 1000,
                                                    self.n_samples / 273,
                                                    self.data.shape))
        else:
            for i in range(self.iterations):
                self.logger.debug('simulating measurement cycle #{} of {}'.format(i, self.iterations))
                self.simulate_measure()

    def on_sim_clock(self):
        if not self.should_stop:
            self.logger.debug('simulating measurement cycle')
            t0 = time.time()

            self.data = simulate_measure(self.data, function='sech2_fwhm', args=[.5, -2, .085, 1], amplitude=10)
            dt = time.time() - t0
            time.sleep(max(self.n_samples / 273000 - dt, 0))
            self.newData.emit(self.data)
            self.logger.debug(
                'simulated data in {:.2f} ms - real would take {:.2f} - '
                'outputting array of shape {}'.format(dt * 1000,
                                                      self.n_samples / 273,
                                                      self.data.shape))




def simulate_measure(data, function='sech2_fwhm', args=[.5, -2, .085, 1], amplitude=10, mode='triggered'):
    args_ = args[:]
    step = parse_setting('fastscan', 'shaker_position_step')
    ps_per_step = parse_setting('fastscan', 'shaker_ps_per_step')  # ADC step size - corresponds to 25fs

    if function == 'gauss_fwhm':
        f = gaussian_fwhm
        args_[1] *= step / ps_per_step  # transform ps to voltage
        args_[2] *= step / ps_per_step  # transform ps to voltage
    elif function == 'gaussian':
        f = gaussian
        step = parse_setting('fastscan', 'shaker_position_step')
        args_[1] *= step / ps_per_step  # transform ps to voltage
        args_[2] *= step / ps_per_step  # transform ps to voltage
        args_.pop(0)
        args_.pop(-1)
    elif function == 'sech2_fwhm':
        f = sech2_fwhm
        step = parse_setting('fastscan', 'shaker_position_step')
        args_[1] *= step / ps_per_step  # transform ps to voltage
        args_[2] *= step / ps_per_step  # transform ps to voltage
    elif function == 'transient_1expdec':
        f = transient_1expdec
        step = parse_setting('fastscan', 'shaker_position_step')

        args_ = [2, 20, 1, 1, .01, -10]
        args_[1] *= step / ps_per_step  # transform ps to voltage
        args_[2] *= step / ps_per_step  # transform ps to voltage
        args_[5] *= step / ps_per_step  # transform ps to voltage
    else:
        raise NotImplementedError('no funcion called {}, please use gauss or sech2'.format(function))
    #########
    n = np.arange(len(data[0]))
    noise = np.random.rand(len(n))
    if mode == 'continuous':
        phase = noise[0] * 2 * np.pi
    else:
        phase = 0
    amplitude = amplitude * step / ps_per_step * (1 + .02 * np.random.uniform(-1, 1))

    data[0, :] = np.cos(2 * np.pi * n / 30000 + phase) * amplitude / 2  # in volt

    data[1, 1::2] = data[0, 1::2] / 3
    data[1, ::2] = f(data[0, ::2], *args_) + noise[::2] + data[0, ::2] / 3
    data[2, ::2] = True
    data[2, 1::2] = False

    return data
