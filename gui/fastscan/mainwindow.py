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
import pyqtgraph as pg
import qdarkstyle
import xarray as xr
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QPushButton, \
    QRadioButton, QLabel, QLineEdit, QSpinBox

from gui.fastscan.plotwidget import FastScanPlotWidget
from measurement.fastscan.threadmanager import FastScanThreadManager
from utilities.qt import SpinBox, labeled_qitem, make_timer
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

        self.main_clock = make_timer(1000. / 60, self.on_main_clock, start=True)
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
        self.start_button.clicked.connect(self.data_manager.start_streamer)
        self.stop_button = QPushButton('stop')
        acquisition_box_layout.addWidget(self.stop_button, 0, 1, 1, 1)
        self.stop_button.clicked.connect(self.data_manager.stop_streamer)
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
        self.n_averages_spinbox.setValue(10)
        # self.n_averages_spinbox.valueChanged[int].connect(self.set_n_averages)
        self.n_averages_spinbox.valueChanged[int].connect(lambda: write_setting())

        acquisition_box_layout.addWidget(QLabel('Averages: '), 2, 0, 1, 1)
        acquisition_box_layout.addWidget(self.n_averages_spinbox, 2, 1, 1, 1)

        # ----------------------------------------------------------------------
        # Settings Box
        # ----------------------------------------------------------------------
        settings_box = QGroupBox('settings')
        layout.addWidget(settings_box)
        settings_box_layout = QGridLayout()
        settings_box.setLayout(settings_box_layout)

        settings_items = []

        self.spinbox_n_samples = SpinBox(
            name='n° of samples', layout_list=settings_items,
            type=int, value=self.settings['n_samples'], step=1, max='max')
        self.spinbox_n_samples.valueChanged.connect(self.set_n_samples)

        for item in settings_items:
            settings_box_layout.addWidget(labeled_qitem(*item))
        self.label_processor_fps = QLabel('FPS: 0')
        settings_box_layout.addWidget(self.label_processor_fps)

        self.radio_dark_control = QRadioButton('Dark Control')
        self.radio_dark_control.setChecked(parse_setting('fastscan', 'dark_control'))
        settings_box_layout.addWidget(self.radio_dark_control)

        self.apply_settings_button = QPushButton('Apply')
        settings_box_layout.addWidget(self.apply_settings_button)
        # self.apply_settings_button.clicked.connect(self.apply_settings)

        # ----------------------------------------------------------------------
        # Autocorrelation Box
        # ----------------------------------------------------------------------

        autocorrelation_box = QGroupBox('Autocorrelation')
        autocorrelation_box_layout = QGridLayout()
        autocorrelation_box.setLayout(autocorrelation_box_layout)

        self.fit_off_checkbox = QRadioButton('Off')
        autocorrelation_box_layout.addWidget(self.fit_off_checkbox, 0, 0, 1, 1)
        self.fit_gauss_checkbox = QRadioButton('last curve')
        autocorrelation_box_layout.addWidget(self.fit_gauss_checkbox, 0, 1, 1, 1)
        self.fit_sech2_checkbox = QRadioButton('average')
        autocorrelation_box_layout.addWidget(self.fit_sech2_checkbox, 0, 2, 1, 1)

        self.fit_off_checkbox.setChecked(True)

        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.fit_report_label = QLabel('Fit parameters:\n')
        autocorrelation_box_layout.addWidget(self.fit_report_label, 2, 0)
        self.pulse_duration_label = QLabel('0 fs')

        self.pulse_duration_label.setFont(font)

        autocorrelation_box_layout.addWidget(QLabel('Pulse duration:'), 3, 0)
        autocorrelation_box_layout.addWidget(self.pulse_duration_label, 3, 1)

        layout.addWidget(autocorrelation_box)
        # layout.addItem(self.__verticalSpacer)

        # ----------------------------------------------------------------------
        # Save Box
        # ----------------------------------------------------------------------

        save_box = QGroupBox('Save')
        savebox_layout = QHBoxLayout()
        save_box.setLayout(savebox_layout)
        self.save_name_ledit = QLineEdit('D:/data/fastscan/test01')
        savebox_layout.addWidget(self.save_name_ledit)
        self.save_data_button = QPushButton('Save')
        savebox_layout.addWidget(self.save_data_button)
        self.save_data_button.clicked.connect(self.save_data)
        layout.addWidget(save_box)

        return widget

    def on_main_clock(self):
        pass
        # x = np.linspace(0, 99, 100)
        # y = np.random.rand(100)
        # # self.visual_widget.add_main_plot_line('test',(255,255,255))
        # self.visual_widget.plot_main('test', x, y)

    def initialize_data_manager(self):

        manager = FastScanThreadManager()
        manager.newProcessedData.connect(self.on_processed_data)
        manager.newStreamerData.connect(self.on_streamer_data)
        manager.newFitResult.connect(self.on_fit_result)
        manager.error.connect(self.on_thread_error)

        manager_thread = QtCore.QThread()
        manager.moveToThread(manager_thread)
        manager_thread.start()

        return manager, manager_thread

    def toggle_simulation_mode(self):
        write_setting(self.radio_simulate.isChecked(), 'fastscan', 'simulate')

    def toggle_darkcontrol_mode(self):
        write_setting(self.radio_simulate.isChecked(), 'fastscan', 'dark_control')

    @QtCore.pyqtSlot(xr.DataArray)
    def on_processed_data(self, data_array):
        try:
            t0 = self.processor_tick
            self.processor_tick = time.time()
            if len(self.fps_l) >= 100:
                self.fps_l.pop(0)
            self.fps_l.append(1. / (self.processor_tick - t0))
            fps = np.mean(self.fps_l)
            self.label_processor_fps.setText('FPS: {:.2f}'.format(fps))
        except:
            self.processor_tick = time.time()
        self.visual_widget.append_curve(data_array)
        self.logger.debug('recieved processed data as {}'.format(type(data_array)))

    @QtCore.pyqtSlot(dict)
    def on_fit_result(self, fitDict):

        self.pulse_duration_label.setText('{:.3} ps'.format(fitDict['popt'][2]))

    def on_streamer_data(self, data):
        n_samples = data.shape[1]
        x = np.linspace(0, n_samples - 1, n_samples)
        self.visual_widget.plot_secondary('stage pos', x=x, y=data[0])
        self.visual_widget.plot_secondary('raw signal', x=x, y=data[1])

    def start_acquisition(self):
        self.data_manager.create_streamer()
        self.data_manager.start_streamer()

    def stop_acquisition(self):
        self.data_manager.stop_streamer()

    def reset_data(self):
        self.data_manager.reset_data()

    def set_n_samples(self, var):
        self.data_manager.n_samples = var

    @QtCore.pyqtSlot(int)
    def set_n_averages(self, val):
        self.data_manager.n_averages = val

    def save_data(self):
        filename = self.save_name_ledit.text()
        self.data_manager.save_data(str(filename))

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
