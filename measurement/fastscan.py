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
import os
import logging
import multiprocessing as mp
import time

import nidaqmx
import numpy as np
import xarray as xr
from PyQt5 import QtCore
from nidaqmx import stream_readers
from nidaqmx.constants import Edge, AcquisitionType

from instruments.delaystage import DelayStage
from instruments.lockinamplifier import LockInAmplifier
from measurement.core import Experiment,Worker
from utilities.math import gaussian, gaussian_fwhm, sech2_fwhm, transient_1expdec
from utilities.math import monotonically_increasing
from utilities.qt import make_timer


class FastScan(Experiment):
    __TYPE = 'stepscan'

    def __init__(self, file=None, **kwargs):
        super().__init__(file=file, **kwargs)
        self.logger = logging.getLogger('{}.StepScan'.format(__name__))
        self.logger.info('Created instance of StepScan.')

        self.required_instruments = [LockInAmplifier, DelayStage]

        self.worker = FastScanWorker
        # define settings to pass to worker. these can be set as variables,
        # since they are class properties! see below...
        self.measurement_settings = {'averages': 2,
                                     'stage_positions': np.linspace(-1, 3, 10),
                                     'time_zero': -.5,
                                     }

    @property
    def stage_positions(self):
        return self.measurement_settings['stage_positions']

    @stage_positions.setter
    def stage_positions(self, array):
        if isinstance(array, list):
            array = np.array(array)
        assert isinstance(array, np.ndarray), 'must be a 1d array'
        assert len(array.shape) == 1, 'must be a 1d array'
        assert monotonically_increasing(array), 'array must be monotonically increasing'
        max_resolution = 0
        for i in range(len(array) - 1):
            step = array[i + 1] - array[i]
            if step < max_resolution:
                max_resolution = step
        self.logger.info('Stage positions changed: {} steps'.format(len(array)))
        self.logger.debug(
            'Current stage_positions configuration: {} steps from {} to {} with max resolution {}'.format(len(array),
                                                                                                          array[0],
                                                                                                          array[-1],
                                                                                                          max_resolution))

        self.measurement_settings['stage_positions'] = array

    @property
    def averages(self):
        return self.measurement_settings['averages']

    @averages.setter
    def averages(self, n):
        assert isinstance(n, int), 'cant run over non integer loops!'
        assert n > 0, 'cant run a negative number of loops!!'
        self.logger.info('Changed number of averages to {}'.format(n))
        self.measurement_settings['averages'] = n

    @property
    def time_zero(self):
        return self.measurement_settings['time_zero']

    @time_zero.setter
    def time_zero(self, t0):
        assert isinstance(t0, float) or isinstance(t0, int), 't0 must be a number!'
        self.logger.info('Changed time zero to {}'.format(t0))
        self.measurement_settings['time_zero'] = t0


class FastScanWorker(Worker):
    """ Subclass of Worker, designed to perform step scan measurements.

    Signals Emitted:

        finished (dict): at end of the scan, emits the results stored over the
            whole scan.
        newData (dict): emitted at each measurement point. Usually contains a
            dictionary with the last measured values toghether with scan
            current_step information.

    **Experiment Input required**:

    settings:
        stagePositions, lockinParametersToRead, dwelltime, numberOfScans
    instruments:
        lockin, stage

    """

    def __init__(self, file, base_instrument, parameters, **kwargs):
        super().__init__(file, base_instrument, parameters, **kwargs)
        self.logger = logging.getLogger('{}.Worker'.format(__name__))
        self.logger.debug('Created a "Worker" instance')

        self.check_requirements()
        self.single_measurement_steps = len(self.stage_positions) * self.averages
        self.parameters_to_measure = ['X', 'Y']
        self.logger.info('Initialized worker with single scan steps: {}'.format(self.single_measurement_steps))

    def check_requirements(self):
        assert hasattr(self, 'averages'), 'No number of averages was passed!'
        assert hasattr(self, 'stage_positions'), 'no values of the stage positions were passed!'
        assert hasattr(self, 'time_zero'), 'Need to tell where time zero is!'
        assert hasattr(self, 'lockin'), 'No Lockin Amplifier found: attribute name should be "lockin"'
        assert hasattr(self, 'delay_stage'), 'No stage found: attribute name should be "delay_stage"'

        self.logger.info('worker has all it needs. Ready to measure_avg!')

    def measure(self):
        """ Step Scan specific project procedure.

        Performs numberOfScans scans in which each moves the stage to the position defined in stagePositions, waits
        for the dwelltime, and finally records the values contained in lockinParameters from the Lock-in amplifier.
        """
        raise NotImplementedError('no Fast Scan measurement implemented.')


class FastScanThreadManager(QtCore.QObject):
    """
    This class manages the streamer processor and fitter workers for the fast
    scan data acquisition and processing.

    """
    newStreamerData = QtCore.pyqtSignal(np.ndarray)
    newProcessedData = QtCore.pyqtSignal(xr.DataArray)
    acquisitionStopped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(np.ndarray)
    error = QtCore.pyqtSignal(Exception)

    def __init__(self, settings=None):
        super().__init__()

        self.logger = logging.getLogger('{}.FastScanThreadManager'.format(__name__))
        self.logger.info('Created Thread Manager')

        self.settings = {'dark_control': False,
                         'processor_buffer': 42000,
                         'streamer_buffer': 42000,
                         'number_of_processors':4,
                         'simulate':True
                         }

        if settings is not None:
            for key,val in settings.items():
                self.settings[key] = val

        self.__stream_queue = mp.Queue()  # Queue where to store unprocessed streamer data
        self.__processor_queue = mp.Queue()

        self.data_dict = {}  # dict containing data to be plotted
        self.processed_averages = None  # container for the xarray dataarray of all averages

        self.res_from_previous = np.zeros((3, 0))

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100.)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start()
        self.lock_data = False

        self.create_processors()
        self.create_streamer()

    @QtCore.pyqtSlot()
    def on_timer(self):
        """ For each idle processor, start evaluating an element in the streamer queue"""
        for processor, ready in zip(self.processors, self.processor_ready):
            if ready and not self.__stream_queue.empty():
                self.logger.debug('processing data with processor {}'.format(processor.id))
                processor.project(self.__stream_queue.get(), use_dark_control=self.dark_control)

    def create_streamer(self):
        self.streamer_thread = QtCore.QThread()

        self.streamer = FastScanStreamer(self.streamer_buffer_size, simulate=self.settings['simulate'])
        self.streamer.newData[np.ndarray].connect(self.on_streamer_data)
        self.streamer.error.connect(self.error.emit)
        # self.streamer.finished.connect(self.on_streamer_finished)

        self.streamer.moveToThread(self.streamer_thread)
        self.streamer_thread.started.connect(self.streamer.start_acquisition)

    @QtCore.pyqtSlot()
    def start_streamer(self):
        self.streamer_thread.start()
        self.logger.info('FastScanStreamer started')
        self.logger.debug('streamer settings: {}'.format(self.settings))

    @QtCore.pyqtSlot()
    def stop_streamer(self):
        self.logger.debug('FastScan Streamer is stopping.')
        self.streamer.stop_acquisition()
        self.streamer_thread.exit()

    @QtCore.pyqtSlot(np.ndarray)
    def on_streamer_data(self, streamer_data):
        """divide data in smaller chunks, for faster data processing.

        Splits data from streamer in chunks whose size is defined by
        self.processor_buffer_size. If the last chunk is smaller than this, it keeps it
        and will append the next data recieved to it.
        """
        try:
            if self.rest_from_previous.shape[1] > 0:
                streamer_data = np.append(self.rest_from_previous, streamer_data, axis=1)
        except:
            pass
        n_chunks = 1#streamer_data.shape[1] // self.processor_buffer_size

        chunks = np.array_split(streamer_data, n_chunks, axis=1)
        if chunks[-1].shape[1] < self.processor_buffer_size:
            self.rest_from_previous = chunks.pop(-1)
        for chunk in chunks:
            self.__stream_queue.put(chunk)

        self.logger.debug('added {} chunks to queue'.format(n_chunks))
        self.newStreamerData.emit(streamer_data)

    def create_processors(self,timeout=1000):
        """ create n_processors number of threads for processing streamer data"""
        if not hasattr(self,'processor_ready'):
            self.processors = []
            self.processor_threads = []
            self.processor_ready = []

        for i in range(self.number_of_processors):
            self.processors.append(FastScanProcessor(i))
            self.processor_threads.append(QtCore.QThread())
            self.processor_ready.append(False)
            self.processors[i].newData[np.ndarray].connect(self.on_processor_data)
            self.processors[i].error.connect(self.error.emit)
            self.processors[i].isReady.connect(self.set_processor_ready)
            # self.processors[i].newDatadict.connect(self.overwrite_datadict)

            # self.processors[i].finished.connect(self.on_processor_finished)

            self.processors[i].moveToThread(self.processor_threads[i])
            self.processor_threads[i].started.connect(self.processors[i].initialize)
            self.processor_threads[i].start()

    @QtCore.pyqtSlot(int)
    def set_processor_ready(self, id):
        self.processor_ready[id] = True

    @QtCore.pyqtSlot(xr.DataArray)
    def on_processor_data(self, processed_dataarray):
        """ called when new processed data is available
        This emits data to the main window, so it can be plotted..."""
        # TODO: add save data
        self.__processor_queue.put(processed_dataarray)
        self.newProcessedData.emit(processed_dataarray)

    @QtCore.pyqtSlot()
    def reset_data(self):
        pass  # TODO: make this

    @QtCore.pyqtSlot()
    def close(self):
        self.stop_streamer()
        for thread in self.processor_threads:
            thread.exit()

    ### Properties

    @property
    def processor_buffer_size(self):
        return self.settings['processor_buffer']

    @processor_buffer_size.setter
    def processor_buffer_size(self, buffer_size):
        assert 0 < buffer_size < 1000000
        assert isinstance(buffer_size, int)
        if not self.streamer_thread.isRunnung():
            self.settings['processor_buffer'] = buffer_size
        else:
            self.logger.warning('Cannot change buffer size while streamer is running.')

    @property
    def streamer_buffer_size(self):
        return self.settings['streamer_buffer']

    @streamer_buffer_size.setter
    def streamer_buffer_size(self, buffer_size):
        assert 0 < buffer_size < 1000000
        assert isinstance(buffer_size, int)
        if not self.streamer_thread.isRunnung():
            self.settings['streamer_buffer'] = buffer_size
        else:
            self.logger.warning('Cannot change buffer size while streamer is running.')

    @property
    def dark_control(self):
        return self.settings['dark_control']

    @dark_control.setter
    def dark_control(self, val):
        assert isinstance(val, bool), 'dark control must be boolean.'
        self.settings['dark_control'] = val

    @property
    def simulate(self):
        return self.settings['simulate']

    @simulate.setter
    def simulate(self,val):
        assert isinstance(val,bool), 'simulate attribute should be boolean'
        self.settings['simulate'] = val

    @property
    def shaker_amplitude(self):
        return self.settings['shaker_amplitude']
    @shaker_amplitude.setter
    def shaker_amplitude(self,val):
        assert 0<val<300, 'shaker amplitude must be between 0 and 300 ps'
        self.settings['shaker_amplitude'] = val

    @property
    def number_of_processors(self):
        return self.settings['number_of_processors']

    @number_of_processors.setter
    def number_of_processors(self, val):
        assert isinstance(val, int), 'dark control must be boolean.'
        assert val < os.cpu_count(), 'Too many processors, cant be more than cpu count: {}'.format(os.cpu_count())
        self.settings['number_of_processors'] = val
        self.create_processors()



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

    def simulate_measure(self, function='sech2_fwhm', args=[1,0,.1,1], amplitude=10):
        data = self.data
        t0 = time.time()
        args_ = args[:]

        if function == 'gauss_fwhm':
            f = gaussian_fwhm
            step = 0.00152587890625
            args_[1] *= step # transform ps to voltage
            args_[2] *= step # transform ps to voltage
        elif function == 'gaussian':
            f = gaussian
            step = 0.00152587890625
            args_[1] *= step # transform ps to voltage
            args_[2] *= step # transform ps to voltage
            args_.pop(0)
            args_.pop(-1)
        elif function == 'sech2_fwhm':
            f = sech2_fwhm
            step = 0.00152587890625
            args_[1] *= step # transform ps to voltage
            args_[2] *= step # transform ps to voltage
        elif function == 'transient_1expdec':
            f = transient_1expdec
            step = 0.00152587890625
            args_ = [2,20,1,1,.01,-10]
            args_[1] *= step  # transform ps to voltage
            args_[2] *= step  # transform ps to voltage
            args_[5] *= step  # transform ps to voltage

        else:
            raise NotImplementedError('no funcion called {}, please use gauss or sech2'.format(function))
        #########
        n = np.arange(len(data[0]))
        noise = np.random.rand(len(n))
        phase = noise[0] * 2 * np.pi

        amplitude = amplitude*0.00152587890625 * (1 + .02 * np.random.uniform(-1, 1))

        data[0, :] = np.cos(2 * np.pi * n / 30000 + phase) * amplitude / 2  # in volt

        data[1, 1::2] = data[0, 1::2] / 3
        data[1,  ::2] = f(data[0, ::2], *args_) + noise[::2] + data[0, ::2] / 3
        data[2,  ::2] = True
        data[2, 1::2] = False
        ####
        dt = time.time() - t0
        time.sleep(max(self.n_samples / 273000 - dt, 0))
        self.logger.debug(
            'simulated data in {:.2f} ms - real would take {:.2f} - '
            'outputting array of {}'.format(dt * 1000,self.n_samples / 273,self.data.shape))

        self.newData.emit(self.data)


class FastScanProcessor(QtCore.QObject):
    isReady = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(xr.DataArray)
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
        self.logger.debug('Processor ID:{} started processing data with shape {}'.format(self.id,stream_data.shape))
        t0 = time.time()
        shaker_positions = stream_data[0]
        signal = stream_data[1]
        dark_control = stream_data[2]

        step = 0.000152587890625  # ADC step size - corresponds to 25fs
        # consider 0.1 ps step size from shaker digitalized signal,
        # should be considering the 2 passes through the shaker
        step_to_time_factor = .1
        minpos = shaker_positions.min()
        min_t = (minpos / step) * step_to_time_factor
        maxpos = shaker_positions.max()
        max_t = (maxpos / step) * step_to_time_factor

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


    @QtCore.pyqtSlot(dict,xr.DataArray)
    def calc_avg(self, data_dict, processor_data):
        try:
            data_dict['all'] = xr.concat([data_dict['all'], processor_data], 'avg')
            if 'avg' in data_dict['all'].dims:
                data_dict['average'] = data_dict['all'][-100:].mean('avg')
        except KeyError:
            data_dict['all'] = processor_data
        self.newDatadict.emit(data_dict)

def main():
    pass


if __name__ == '__main__':
    main()
