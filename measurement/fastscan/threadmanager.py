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
import time
import h5py
import numpy as np
import xarray as xr
from PyQt5 import QtCore

from measurement.fastscan.streamer import FastScanStreamer
from measurement.fastscan.processor import FastScanProcessor
from utilities.settings import parse_setting, parse_category, write_setting


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
    newAverage = QtCore.pyqtSignal(xr.DataArray)
    acquisitionStopped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(np.ndarray)
    error = QtCore.pyqtSignal(Exception)

    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger('{}.FastScanThreadManager'.format(__name__))
        self.logger.info('Created Thread Manager')

        self.__stream_queue = mp.Queue()  # Queue where to store unprocessed streamer data
        self.__processor_queue = mp.Queue()

        self.all_curves = None
        self.running_average = None

        self.should_stop = False

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1.)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start()

        self.create_processors()
        self.create_streamer()

    @QtCore.pyqtSlot()
    def on_timer(self):
        """ For each idle processor, start evaluating an element in the streamer queue"""
        for processor, ready in zip(self.processors, self.processor_ready):

            if ready and not self.__stream_queue.empty():
                self.logger.debug('processing data with processor {} - queue lenght {}'.format(processor.id,self.__stream_queue.qsize()))
                processor.project(self.__stream_queue.get(), use_dark_control=self.dark_control)
            elif self.should_stop:
                self.streamer_thread.exit()

    def create_streamer(self):
        self.streamer_thread = QtCore.QThread()

        self.streamer = FastScanStreamer()
        self.streamer.newData[np.ndarray].connect(self.on_streamer_data)
        self.streamer.error.connect(self.error.emit)
        # self.streamer.finished.connect(self.on_streamer_finished)

        self.streamer.moveToThread(self.streamer_thread)
        self.streamer_thread.started.connect(self.streamer.start_acquisition)

    @QtCore.pyqtSlot()
    def start_streamer(self):
        self.should_stop = False
        self.streamer_thread.start()
        self.logger.info('FastScanStreamer started')
        self.logger.debug('streamer settings: {}'.format(parse_category('fastscan')))

    @QtCore.pyqtSlot()
    def stop_streamer(self):
        self.logger.debug('\n\nFastScan Streamer is stopping.\n\n')
        self.streamer.stop_acquisition()
        self.should_stop = True

    @QtCore.pyqtSlot(np.ndarray)
    def on_streamer_data(self, streamer_data): #TODO: remove or change the queue method
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
        if chunks[-1].shape[1] < self.n_samples:
            self.rest_from_previous = chunks.pop(-1)
        for chunk in chunks:
            self.__stream_queue.put(chunk)

        self.logger.debug('added {} chunks to queue'.format(n_chunks))
        self.newStreamerData.emit(streamer_data)

    def create_processors(self): # TODO: change to QTrheadPool
        """ create n_processors number of threads for processing streamer data"""
        if not hasattr(self, 'processor_ready'):
            self.processors = []
            self.processor_threads = []
            self.processor_ready = []

        for i in range(self.n_processors):
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
        # self.__processor_queue.put(processed_dataarray)
        self.newProcessedData.emit(processed_dataarray)
        t0 = time.time()
        if self.all_curves is None:
            self.all_curves = processed_dataarray
            self.running_average = processed_dataarray.dropna('time')

        else:
            self.all_curves = xr.concat([self.all_curves[-self.n_averages+1:], processed_dataarray], 'avg')
            self.running_average = self.all_curves.mean('avg').dropna('time')

        for processor, ready in zip(self.processors, self.processor_ready):
            if ready:
                processor.fit_sech2(self.running_average)
                break
        self.newProcessedData.emit(processed_dataarray)
        self.newAverage.emit(self.running_average)
        self.logger.debug('calculated average in {:.2f} ms'.format((time.time()-t0)*1000))

    @QtCore.pyqtSlot(dict)
    def on_fit_result(self,fitDict):
        self.newFitResult.emit(fitDict)

    @QtCore.pyqtSlot()
    def reset_data(self):
        #TODO: add popup check window
        self.running_average = None
        self.all_curves = None

    def save_data(self,filename):
        if not '.h5' in filename:
            filename += '.h5'

        with h5py.File(filename, 'w') as f:
            # f.create_dataset('/raw/spos', data=data[0], shape=(42000,), dtype=float)
            # f.create_dataset('/raw/signal', data=data[1], shape=(42000,), dtype=float)
            # f.create_dataset('/raw/dark_control', data=data[2], shape=(42000,), dtype=float)

            f.create_dataset('/all_data/data', data=self.all_curves.values)
            f.create_dataset('/all_data/time_axis', data=self.all_curves.time)
            f.create_dataset('/avg/data', data=self.running_average.values)
            f.create_dataset('/avg/time_axis', data=self.running_average.time)

    @QtCore.pyqtSlot()
    def close(self):
        self.stop_streamer()
        for thread in self.processor_threads:
            thread.exit()

    ### Properties

    @property
    def dark_control(self):
        return parse_setting('fastscan','dark_control')

    @dark_control.setter
    def dark_control(self, val):
        assert isinstance(val, bool), 'dark control must be boolean.'
        write_setting(val, 'fastscan','dark_control')

    @property
    def n_processors(self):
        return parse_setting('fastscan','n_processors')

    @n_processors.setter
    def n_processors(self, val):
        assert isinstance(val, int), 'dark control must be boolean.'
        assert val < os.cpu_count(), 'Too many processors, cant be more than cpu count: {}'.format(os.cpu_count())
        write_setting(val, 'fastscan','n_processors')
        self.create_processors()

    @property
    def n_averages(self):
        try:
            return self._n_averages
        except:
            self._n_averages = parse_setting('fastscan','n_averages')
            return self._n_averages

    @n_averages.setter
    def n_averages(self, val):
        assert val > 0, 'cannot set below 1'
        write_setting(val, 'fastscan','n_averages')
        self._n_averages = val
        self.logger.debug('n_averages set to {}'.format(val))

    @property
    def n_samples(self):
        return parse_setting('fastscan','n_samples')

    @n_samples.setter
    def n_samples(self, val):
        assert val > 0, 'cannot set below 1'
        write_setting(val, 'fastscan','n_samples')
        self.logger.debug('n_samples set to {}'.format(val))


if __name__ == '__main__':
    main()