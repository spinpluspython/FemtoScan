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
import multiprocessing as mp
import os

import numpy as np
import xarray as xr
from PyQt5 import QtCore

from measurement.fastscan.streamer import FastScanStreamer
from measurement.fastscan.processor import FastScanProcessor


def main():
    pass


class FastScanThreadManager(QtCore.QObject):
    """
    This class manages the streamer processor and fitter workers for the fast
    scan data acquisition and processing.

    """
    newStreamerData = QtCore.pyqtSignal(np.ndarray)
    newProcessedData = QtCore.pyqtSignal(xr.DataArray)
    newFitResult = QtCore.pyqtSignal(dict)
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
                         'number_of_processors': 4,
                         'simulate': True
                         }

        if settings is not None:
            for key, val in settings.items():
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
        n_chunks = 1  # streamer_data.shape[1] // self.processor_buffer_size

        chunks = np.array_split(streamer_data, n_chunks, axis=1)
        if chunks[-1].shape[1] < self.processor_buffer_size:
            self.rest_from_previous = chunks.pop(-1)
        for chunk in chunks:
            self.__stream_queue.put(chunk)

        self.logger.debug('added {} chunks to queue'.format(n_chunks))
        self.newStreamerData.emit(streamer_data)

    def create_processors(self, timeout=1000):
        """ create n_processors number of threads for processing streamer data"""
        if not hasattr(self, 'processor_ready'):
            self.processors = []
            self.processor_threads = []
            self.processor_ready = []

        for i in range(self.number_of_processors):
            self.processors.append(FastScanProcessor(i))
            self.processor_threads.append(QtCore.QThread())
            self.processor_ready.append(False)
            self.processors[i].newData[np.ndarray].connect(self.on_processor_data)
            self.processors[i].newFit[dict].connect(self.on_fit_result)
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
        for processor, ready in zip(self.processors, self.processor_ready):
            if ready:
                processor.fit_sech2(processed_dataarray)
                print('############## Attempting to fit ###############')
                break
        self.newProcessedData.emit(processed_dataarray)

    @QtCore.pyqtSlot(dict)
    def on_fit_result(self,fitDict):
        print('######### fit result: {}'.format(fitDict['popt']))
        self.newFitResult.emit(fitDict)

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
    def simulate(self, val):
        assert isinstance(val, bool), 'simulate attribute should be boolean'
        self.settings['simulate'] = val

    @property
    def shaker_amplitude(self):
        return self.settings['shaker_amplitude']

    @shaker_amplitude.setter
    def shaker_amplitude(self, val):
        assert 0 < val < 300, 'shaker amplitude must be between 0 and 300 ps'
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


if __name__ == '__main__':
    main()