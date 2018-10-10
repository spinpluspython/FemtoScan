# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""


def raise_Qerror(self, doingWhat, errorHandle, type='Warning', popup=True):
    """ opens a dialog window showing the error"""
    errorMessage = 'Thread Error while {0}:\n{1}'.format(doingWhat, errorHandle)
    print(errorMessage)
    if popup:
        errorDialog = QtWidgets.QMessageBox()
        errorDialog.setText(errorMessage)
        if type == 'Warning':
            errorDialog.setIcon(QtWidgets.QMessageBox.Warning)
        elif type == 'Critical':
            errorDialog.setIcon(QtWidgets.QMessageBox.Critical)
        errorDialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        errorDialog.exec_()


def main():
    pass


if __name__ == '__main__':
    main()
