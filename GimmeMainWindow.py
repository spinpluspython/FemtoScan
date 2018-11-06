import sys
from gui import TestingFinalMainWidget
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import QtCore

class MainWindow(QMainWindow, TestingFinalMainWidget.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.scanWidget.setTimeScale.connect(self.make_timescale)
        self.settingsWidget.setValue.connect(self.setSettingsValue)

    @QtCore.pyqtSlot(list,list)
    def make_timescale(self,l1,l2):
        """
        
        Args:
            l1: 
            l2: 

        Returns:

        """
        print('from a signal')
        print(l1,l2)

    @QtCore.pyqtSlot(str, str, str)
    def setSettingsValue(selfself, s1, s2, s3):
        print(s1+", "+s2+", "+s3)


app = QApplication(sys.argv)
form = MainWindow()
form.show()
app.exec()