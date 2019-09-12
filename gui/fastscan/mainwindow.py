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
import os

import numpy as np
import pyqtgraph as pg
import qdarkstyle
import xarray as xr
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, \
    QGroupBox, QGridLayout, QPushButton, QDoubleSpinBox, \
    QRadioButton, QLabel, QLineEdit, QSpinBox, QCheckBox, QComboBox
from PyQt5.QtWidgets import QSizePolicy
from scipy.signal import butter, filtfilt

from gui.fastscan.plotwidget import FastScanPlotWidget
from measurement.fastscan.threadmanager import FastScanThreadManager
from utilities.settings import parse_category, parse_setting, write_setting


class FastScanMainWindow(QMainWindow):

    def __init__(self):
        super(FastScanMainWindow, self).__init__()
        self.logger = logging.getLogger('{}.FastScanMainWindow'.format(__name__))
        self.logger.info('Created MainWindow')

        self.setWindowTitle('Fast Scan')
        self.setGeometry(100, 50, 1152, 768)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage('ready')
        # set the cool dark theme and other plotting settings
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        pg.setConfigOption('background', (25, 35, 45))
        pg.setConfigOption('foreground', 'w')
        pg.setConfigOptions(antialias=True)

        #########################
        #   define attributes    #
        #########################

        self.settings = parse_category('fastscan')  # import all

        self.data_manager, self.data_manager_thread = self.initialize_data_manager()

        self.fps_l = []

        self.main_clock = QtCore.QTimer()
        self.main_clock.setInterval(.100)
        self.main_clock.start()
        self.main_clock.timeout.connect(self.on_main_clock)

        self.setupUi()
        self.show()

    def setupUi(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout()
        central_widget.setLayout(central_layout)

        self.__verticalSpacer = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        control_widget = self.make_controlwidget()
        self.visual_widget = FastScanPlotWidget()
        self.visual_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        control_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        main_splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        main_splitter.addWidget(control_widget)
        main_splitter.addWidget(self.visual_widget)
        # main_splitter.setStretchFactor(0, 5)

        central_layout.addWidget(main_splitter)

    def make_controlwidget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # ----------------------------------------------------------------------
        # Acquisition Box
        # ----------------------------------------------------------------------

        acquisition_box = QGroupBox('Acquisition')
        layout.addWidget(acquisition_box)
        acquisition_box_layout = QGridLayout()
        acquisition_box.setLayout(acquisition_box_layout)

        self.start_button = QPushButton('start')
        acquisition_box_layout.addWidget(self.start_button, 0, 0, 1, 1)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button = QPushButton('stop')
        acquisition_box_layout.addWidget(self.stop_button, 0, 1, 1, 1)
        self.stop_button.clicked.connect(self.stop_acquisition)
        # self.stop_button.setEnabled(False)

        self.reset_button = QPushButton('reset')
        acquisition_box_layout.addWidget(self.reset_button, 1, 1, 1, 1)
        self.reset_button.clicked.connect(self.reset_data)
        self.reset_button.setEnabled(True)

        self.radio_simulate = QRadioButton('Simulate')
        self.radio_simulate.setChecked(parse_setting('fastscan', 'simulate'))
        acquisition_box_layout.addWidget(self.radio_simulate, 1, 0, 1, 1)
        self.radio_simulate.clicked.connect(self.toggle_simulation_mode)

        self.n_averages_spinbox = QSpinBox()
        self.n_averages_spinbox.setMinimum(1)
        self.n_averages_spinbox.setMaximum(999999)

        self.n_averages_spinbox.setValue(parse_setting('fastscan', 'n_averages'))
        # self.n_averages_spinbox.valueChanged[int].connect(self.set_n_averages)
        self.n_averages_spinbox.valueChanged[int].connect(lambda x: write_setting(x, 'fastscan', 'n_averages'))

        acquisition_box_layout.addWidget(QLabel('Averages: '), 2, 0, 1, 1)
        acquisition_box_layout.addWidget(self.n_averages_spinbox, 2, 1, 1, 1)

        # ----------------------------------------------------------------------
        # Save Box
        # ----------------------------------------------------------------------

        save_box = QGroupBox('Save')
        savebox_layout = QGridLayout()
        layout.addWidget(save_box)

        save_box.setLayout(savebox_layout)
        h5_dir = parse_setting('paths', 'h5_data')
        i = 0
        names = [x for x in os.listdir(h5_dir) if 'noname_' in x]
        filename = ''
        while True:
            filename = 'noname_{:03}'.format(i)
            if f'{filename}.h5' in names:
                i += 1
            else:
                break

        self.save_name_ledit = QLineEdit(filename)
        savebox_layout.addWidget(QLabel('Name:'), 0, 0)
        savebox_layout.addWidget(self.save_name_ledit, 0, 1)
        self.save_dir_ledit = QLineEdit(h5_dir)
        savebox_layout.addWidget(QLabel('dir :'), 1, 0)
        savebox_layout.addWidget(self.save_dir_ledit, 1, 1)

        self.save_all_cb = QCheckBox('Save avgs')
        self.save_all_cb.setToolTip(
            'If Checked, saves all projected average curves, \nelse it only saves the accumulate average trace.')
        savebox_layout.addWidget(self.save_all_cb, 2, 0)
        self.save_all_cb.setChecked(True)

        self.save_data_button = QPushButton('Save')
        savebox_layout.addWidget(self.save_data_button, 2, 1, 2, 2)
        self.save_data_button.clicked.connect(self.save_data)

        # self.autosave_checkbox = QCheckBox('autosave')
        # savebox_layout.addWidget(self.autosave_checkbox,3,0)
        # self.autosave_timeout = QDoubleSpinBox()
        # self.autosave_timeout.setValue(1)
        # savebox_layout.addWidget(QLabel('timeout (s)'),3,1)
        # savebox_layout.addWidget(self.autosave_timeout,3,2)

        self.datasize_label = QLabel('data Size')
        savebox_layout.addWidget(self.datasize_label, 4, 0, 3, 2)

        # ----------------------------------------------------------------------
        # Settings Box
        # ----------------------------------------------------------------------
        settings_box = QGroupBox('settings')
        layout.addWidget(settings_box)
        settings_box_layout = QGridLayout()
        settings_box.setLayout(settings_box_layout)

        settings_items = []

        self.spinbox_n_samples = QSpinBox()
        self.spinbox_n_samples.setMaximum(2147483647)
        self.spinbox_n_samples.setMinimum(100)
        self.spinbox_n_samples.setValue(parse_setting('fastscan', 'n_samples'))
        self.spinbox_n_samples.setSingleStep(100)
        self.spinbox_n_samples.valueChanged.connect(self.set_n_samples)
        settings_box_layout.addWidget(QLabel('n° of samples'), 0, 0)
        settings_box_layout.addWidget(self.spinbox_n_samples, 0, 1)

        self.label_processor_fps = QLabel('FPS: 0')
        # settings_box_layout.addWidget(self.label_processor_fps)

        self.shaker_gain_combobox = QComboBox()
        self.shaker_gain_combobox.addItem('1')
        self.shaker_gain_combobox.addItem('10')
        self.shaker_gain_combobox.addItem('100')

        def set_shaker_gain(val):
            self.data_manager.shaker_gain = val

        self.shaker_gain_combobox.activated[str].connect(set_shaker_gain)
        settings_box_layout.addWidget(QLabel('Shaker Gain'), 1, 0)
        settings_box_layout.addWidget(self.shaker_gain_combobox, 1, 1)

        self.radio_dark_control = QRadioButton('Dark Control')
        self.radio_dark_control.setChecked(parse_setting('fastscan', 'dark_control'))
        settings_box_layout.addWidget(self.radio_dark_control)
        self.radio_dark_control.clicked.connect(self.toggle_darkcontrol_mode)

        # self.filter_frequency_spinbox.setMaximum(1.)
        # self.filter_frequency_spinbox.setMinimum(0.0)

        # self.apply_settings_button.clicked.connect(self.apply_settings)

        # self.apply_settings_button = QPushButton('Apply')
        # settings_box_layout.addWidget(self.apply_settings_button)

        # ----------------------------------------------------------------------
        # Filter Box
        # ----------------------------------------------------------------------
        filter_box = QGroupBox('Filter')
        layout.addWidget(filter_box)
        filter_box_layout = QGridLayout()
        filter_box.setLayout(filter_box_layout)

        self.butter_filter_checkbox = QCheckBox('Butter')
        filter_box_layout.addWidget(self.butter_filter_checkbox, 0, 0)
        self.filter_order_spinbox = QSpinBox()
        self.filter_order_spinbox.setValue(2)
        filter_box_layout.addWidget(QLabel('Order:'), 0, 1)
        filter_box_layout.addWidget(self.filter_order_spinbox, 0, 2)

        self.filter_frequency_spinbox = QDoubleSpinBox()
        self.filter_frequency_spinbox.setValue(.3)

        filter_box_layout.addWidget(QLabel('Cut (0.-1.):'), 0, 3)
        filter_box_layout.addWidget(self.filter_frequency_spinbox, 0, 4)
        self.butter_filter_checkbox.setChecked(False)

        # ----------------------------------------------------------------------
        # Autocorrelation Box
        # ----------------------------------------------------------------------

        autocorrelation_box = QGroupBox('Autocorrelation')
        autocorrelation_box_layout = QGridLayout()
        autocorrelation_box.setLayout(autocorrelation_box_layout)

        self.calculate_autocorrelation_box = QCheckBox('Fit')
        autocorrelation_box_layout.addWidget(self.calculate_autocorrelation_box)
        self.calculate_autocorrelation_box.setChecked(False)
        self.calculate_autocorrelation_box.clicked.connect(self.toggle_calculate_autocorrelation)

        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        report = '{:^8}|{:^8}|{:^8}|{:^8}\n{:^8.3f}|{:^8.3f}|{:^8.3f}|{:^8.3f}'.format(
            'Amp', 'Xc', 'FWHM', 'off', .0, .0, .0, .0)
        self.autocorrelation_report_label = QLabel(report)

        self.pulse_duration_label = QLabel('0 fs')
        self.pulse_duration_label.setFont(font)
        autocorrelation_box_layout.addWidget(self.calculate_autocorrelation_box, 0, 0, 1, 1)
        autocorrelation_box_layout.addWidget(self.autocorrelation_report_label, 0, 1, 1, 2)
        autocorrelation_box_layout.addWidget(QLabel('Pulse duration:'), 2, 0, 1, 1)
        autocorrelation_box_layout.addWidget(self.pulse_duration_label, 2, 1, 1, 2)

        layout.addWidget(autocorrelation_box)

        # ----------------------------------------------------------------------
        # Stage Control Box
        # ----------------------------------------------------------------------

        # self.delay_stage_widget = DelayStageWidget(self.data_manager.delay_stage)
        # # layout.addWidget(self.delay_stage_widget)
        #
        #
        # shaker_calib_gbox = QGroupBox('Shaker Calibration')
        # shaker_calib_layout = QGridLayout()
        # shaker_calib_gbox.setLayout(shaker_calib_layout)
        # self.shaker_calib_btn = QPushButton('Shaker Calibration')
        # shaker_calib_layout.addWidget(self.shaker_calib_btn,0,0,2,2)
        # self.shaker_calib_btn.clicked.connect(self.on_shaker_calib)
        # self.shaker_calib_iterations = QSpinBox()
        # self.shaker_calib_iterations.setValue(50)
        # self.shaker_calib_iterations.setMinimum(4)
        # self.shaker_calib_iterations.setMaximum(100000)
        # self.shaker_calib_integration = QSpinBox()
        # self.shaker_calib_integration.setValue(5)
        # self.shaker_calib_integration.setMinimum(1)
        # self.shaker_calib_integration.setMaximum(100000)
        #
        # shaker_calib_layout.addWidget(QLabel('iterations:'),0,2,1,1)
        # shaker_calib_layout.addWidget(QLabel('integrations:'),1,2,1,1)
        # shaker_calib_layout.addWidget(self.shaker_calib_iterations,0,3,1,1)
        # shaker_calib_layout.addWidget(self.shaker_calib_integration,1,3,1,1)

        # ----------------------------------------------------------------------
        # Iterative Measurement Box
        # ----------------------------------------------------------------------

        iterative_measurement_box = QGroupBox('Iterative Measurement')
        iterative_measurement_box_layout = QGridLayout()
        iterative_measurement_box.setLayout(iterative_measurement_box_layout)
        layout.addWidget(iterative_measurement_box)

        self.im_save_name = QLineEdit('measurement session name')
        iterative_measurement_box_layout.addWidget(QLabel('Name:'), 0, 0)
        iterative_measurement_box_layout.addWidget(self.im_save_name, 0, 1)
        self.im_save_dir = QLineEdit('D:\\')
        iterative_measurement_box_layout.addWidget(QLabel('dir :'), 1, 0)
        iterative_measurement_box_layout.addWidget(self.im_save_dir, 1, 1)
        self.im_temperatures = QLineEdit('5,10,15,20')
        iterative_measurement_box_layout.addWidget(QLabel('temperatures :'), 2, 0)
        iterative_measurement_box_layout.addWidget(self.im_temperatures, 2, 1)

        self.start_iterative_measurement_button = QPushButton('Start')
        iterative_measurement_box_layout.addWidget(self.start_iterative_measurement_button, 3, 0, 1, 2)
        self.start_iterative_measurement_button.clicked.connect(self.start_iterative_measurement)

        # layout.addWidget(shaker_calib_gbox)

        return widget

    def start_iterative_measurement(self):
        temperatures = [float(x) for x in self.im_temperatures.text().split(',')]
        savename = os.path.join(self.im_save_dir.text(), self.im_save_name.text())
        self.data_manager.start_iterative_measurement(temperatures, savename)

    def on_main_clock(self):
        # self.main_clock.setInterval(self.autosave_timeout.value())
        try:
            streamer_shape = self.data_manager.streamer_average.shape
            projected_shape = self.data_manager.all_curves.shape
        except AttributeError:
            streamer_shape = projected_shape = (0, 0)

        string = 'Data Size :\n streamer: {} - {:10.3f} Kb\n projected: {} - {:10.3f} Kb'.format(
            streamer_shape, np.prod(streamer_shape) / (1024), projected_shape, np.prod(projected_shape) / (1024)
        )
        self.datasize_label.setText(string)
        # if self.autosave_checkbox.isChecked():
        #     try:
        #         self.save_data()
        #     except (TypeError,AttributeError):
        #         pass

    def initialize_data_manager(self):

        manager = FastScanThreadManager()
        manager.newProcessedData.connect(self.on_processed_data)
        manager.newStreamerData.connect(self.on_streamer_data)
        manager.newFitResult.connect(self.on_fit_result)
        manager.newAverage.connect(self.on_avg_data)
        manager.error.connect(self.on_thread_error)

        manager_thread = QtCore.QThread()
        manager.moveToThread(manager_thread)
        manager_thread.start()

        return manager, manager_thread

    def toggle_simulation_mode(self):
        write_setting(self.radio_simulate.isChecked(), 'fastscan', 'simulate')

    def toggle_darkcontrol_mode(self):
        write_setting(self.radio_simulate.isChecked(), 'fastscan', 'dark_control')

    def toggle_calculate_autocorrelation(self):
        self.data_manager._calculate_autocorrelation = self.calculate_autocorrelation_box.isChecked()

    def on_shaker_calib(self):
        self.data_manager.calibrate_shaker(self.shaker_calib_iterations.value(), self.shaker_calib_integration.value())

    @QtCore.pyqtSlot(xr.DataArray)
    def on_processed_data(self, data_array):
        # try:
        #     t0 = self.processor_tick
        #     self.processor_tick = time.time()
        #     if len(self.fps_l) >= 100:
        #         self.fps_l.pop(0)
        #     self.fps_l.append(1. / (self.processor_tick - t0))
        #     fps = np.mean(self.fps_l)
        #     self.label_processor_fps.setText('FPS: {:.2f}'.format(fps))
        # except:
        #     self.processor_tick = time.time()
        self.apply_filter(data_array)
        self.visual_widget.plot_last_curve(data_array)
        self.logger.debug('recieved processed data as {}'.format(type(data_array)))

    @QtCore.pyqtSlot(dict)
    def on_fit_result(self, fitDict):
        self.pulse_duration_label.setText('{:.3f} ps'.format(fitDict['popt'][2] * .65))
        report = '{:^8}|{:^8}|{:^8}|{:^8}\n{:^8.3f}|{:^8.3f}|{:^8.3f}|{:^8.3f}'.format(
            'Amp', 'Xc', 'FWHM', 'off', *fitDict['popt'])
        self.autocorrelation_report_label.setText(report)

        self.visual_widget.plot_fit_curve(fitDict['curve'])

    @QtCore.pyqtSlot(xr.DataArray)
    def on_avg_data(self, da):
        self.apply_filter(da)
        self.visual_widget.plot_avg_curve(da)

    def on_streamer_data(self, data):
        self.visual_widget.plot_stream_curve(data)

    def apply_filter(self, data_array):
        if self.butter_filter_checkbox.isChecked():
            try:
                b, a = butter(2, self.filter_frequency_spinbox.value())
                data_array.data = filtfilt(b, a, data_array)
            except:
                pass

    def start_acquisition(self):
        # self.data_manager.create_streamer()
        self.status_bar.showMessage('Acquisition started')
        self.data_manager.start_streamer()

    def stop_acquisition(self):
        self.status_bar.showMessage('Acquisition Stopped')
        self.data_manager.stop_streamer()

    def reset_data(self):
        self.status_bar.showMessage('Data reset')
        self.data_manager.reset_data()

    def set_n_samples(self, var):
        self.data_manager.n_samples = var

    @QtCore.pyqtSlot(int)
    def set_n_averages(self, val):
        self.data_manager.n_averages = val

    def save_data(self):

        dir = self.save_dir_ledit.text()
        filename = self.save_name_ledit.text()
        filepath = os.path.join(dir, filename)
        self.data_manager.save_data(filepath, all_data=self.save_all_cb.isChecked())
        self.status_bar.showMessage('Successfully saved data as {}'.format(filepath))

    @QtCore.pyqtSlot(Exception)
    def on_thread_error(self, e):
        self.logger.critical('Thread error: {}'.format(e))
        raise e

    def closeEvent(self, event):
        super(FastScanMainWindow, self).closeEvent(event)
        self.logger.info('Closing window: terminating all threads.')
        self.data_manager.close()
        self.data_manager_thread.exit()


if __name__ == '__main__':
    pass
