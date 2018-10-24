# -*- coding: utf-8 -*-

import sys

import sys
import PlotTestWidget
from PyQt5.QtWidgets import QMainWindow, QApplication


def main():
    pass


class MainWindow(QMainWindow, PlotTestWidget.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)


if __name__ == '__main__':
    main()
