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

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,QPushButton
from pyqtgraph.Qt import QtCore, QtGui


class FastScanPlotWidget(QWidget):

    def __init__(self):
        super(FastScanPlotWidget, self).__init__()
        self.logger = logging.getLogger('-.{}.PlotWidget'.format(__name__))
        self.logger.info('Created PlotWidget')

        self.clock = QTimer()
        self.clock.setInterval(1000. / 30)
        self.clock.timeout.connect(self.on_clock)
        self.clock.start()

        self.curves = {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.main_plot_widget = pg.PlotWidget(name='main_plot')
        self.main_plot = self.main_plot_widget.getPlotItem()
        self.setup_plot_widget(self.main_plot_widget, title='Main')
        self.main_plot_widget.showAxis('top', True)
        self.main_plot_widget.showAxis('right', True)
        self.main_plot_widget.showGrid(True, True, .2)
        self.main_plot_widget.setLabel('left', 'Value', units='V')
        self.main_plot_widget.setLabel('bottom', 'Time', units='s')
        self.small_plot_widget = pg.PlotWidget(name='stream_plot')
        self.small_plot = self.small_plot_widget.getPlotItem()
        self.setup_plot_widget(self.small_plot_widget, title='Stream')
        self.small_plot_widget.showAxis('top', True)
        self.small_plot_widget.showAxis('right', True)
        self.small_plot_widget.showGrid(True, True, .2)
        self.small_plot_widget.setLabel('left', 'Value', units='V')
        self.small_plot_widget.setLabel('bottom', 'Time', units='samples')

        # self.small_plot_widget.setMinimumHeight(int(h * .7))
        self.small_plot_widget.setMaximumWidth(400)
        self.small_plot_widget.setMinimumWidth(200)

        controls = QGroupBox('Plot Settings')
        controls_layout = QVBoxLayout()
        controls.setLayout(controls_layout)

        self.cb_last_curve = QCheckBox('last curve')
        controls_layout.addWidget(self.cb_last_curve)
        self.cb_last_curve.setChecked(True)
        self.cb_avg_curve = QCheckBox('average curve')
        controls_layout.addWidget(self.cb_avg_curve)
        self.cb_avg_curve.setChecked(False)

        self.cb_fit_curve = QCheckBox('fit curve')
        controls_layout.addWidget(self.cb_fit_curve)
        self.cb_fit_curve.setChecked(True)

        self.last_curve = self.main_plot_widget.plot(name='last')
        self.last_curve.setPen((pg.mkPen(200, 200, 200)))
        self.avg_curve = self.main_plot_widget.plot(name='avg')
        self.avg_curve.setPen((pg.mkPen(100, 255, 100)))
        self.fit_curve = self.main_plot_widget.plot(name='fit')
        self.fit_curve.setPen((pg.mkPen(255, 100, 100)))

        self.stream_curve = self.small_plot_widget.plot()
        self.stream_curve.setPen((pg.mkPen(255, 100, 100)))

        self.stream_signal_dc0 = self.small_plot_widget.plot()
        self.stream_signal_dc0.setPen((pg.mkPen(100, 255, 100)))
        self.stream_signal_dc1 = self.small_plot_widget.plot()
        self.stream_signal_dc1.setPen((pg.mkPen(100, 100, 255)))

        vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        hsplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        vsplitter.addWidget(self.main_plot_widget)
        vsplitter.addWidget(hsplitter)
        hsplitter.addWidget(controls)
        hsplitter.addWidget(self.small_plot_widget)

        layout.addWidget(vsplitter)

    def setup_plot_widget(self, plot_widget, title='Plot'):
        plot_widget.showAxis('top', True)
        plot_widget.showAxis('right', True)
        plot_widget.showGrid(True, True, .2)
        plot_widget.setLabel('left', 'Value', units='V')
        plot_widget.setLabel('bottom', 'Time', units='s')
        # plot_widget.setLabel('top', title)

    def resizeEvent(self, event):
        h = self.frameGeometry().height()
        w = self.frameGeometry().width()
        self.main_plot_widget.setMinimumHeight(int(h * .7))
        self.main_plot_widget.setMinimumWidth(500)

    def add_curve(self,name,color=(255, 255, 255)):
        self.curves[name] = self.main_plot_widget.plot(name=name)
        self.curves[name].setPen((pg.mkPen(*color)))

    def plot_curve(self,name, da):
        if name in self.curves:
            self.curves[name].setData(da.time * 10 ** -12, da)

    def plot_last_curve(self, da):
        if self.cb_last_curve.isChecked():
            if 'last' not in self.curves:
                self.add_curve('last',color=(200, 200, 200))
            self.plot_curve('last', da)
        else:
            if 'last' in self.curves:
                self.main_plot.removeItem(self.curves.pop('last'))

    def plot_avg_curve(self, da):
        if self.cb_avg_curve.isChecked():
            if 'avg' not in self.curves:
                self.add_curve('avg',color=(255, 100, 100))
            self.plot_curve('avg', da)
        else:
            if 'avg' in self.curves:
                self.main_plot.removeItem(self.curves.pop('avg'))

    def plot_fit_curve(self, da):
        if self.cb_fit_curve.isChecked():
            if 'fit' not in self.curves:
                self.add_curve('fit',color=(100, 255, 100))
            self.plot_curve('fit', da)
        else:
            if 'fit' in self.curves:
                self.main_plot.removeItem(self.curves.pop('fit'))

    def plot_stream_curve(self, data):
        x = np.arange(len(data[0]))
        pos = data[0, :]
        if data[2, 1] > data[2, 0]:
            sig_dc0 = data[1, 1::2]
            sig_dc1 = data[1, 0::2]
        else:
            sig_dc1 = data[1, 1::2]
            sig_dc0 = data[1, 0::2]
        self.stream_curve.setData(x, pos)
        self.stream_signal_dc0.setData(x[::2], sig_dc0)
        self.stream_signal_dc1.setData(x[::2], sig_dc1)

    def on_clock(self):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
