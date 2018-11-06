from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLineEdit, QApplication, QComboBox, QDoubleSpinBox
import  PyQt5.QtWidgets

import PyQt5.QtCore as QtCore

class StackedExample(QWidget):
    setTimeScale = QtCore.pyqtSignal(list, list)


    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.stepAreas = 1
        self.spinnerList = []  # [  [ Start/End, Step ]  , [...]  ,  ...  ]
        self.widgetList = []  # [  [ ComboBox, LineEdit ]  , [...]  ,  ...  ]
        self.lay = QGridLayout(self)
        self.setValuesButton = QPushButton("Set Values")
        self.addButton = QPushButton("Add")
        self.startSpinner = QDoubleSpinBox()
        self.startSpinner.setRange(-999, 999)
        self.startSpinner.setValue(4)
        self.startSpinner.setDecimals(4)

        self.start_endSpinner = QDoubleSpinBox()
        self.start_endSpinner.setRange(-999, 999)
        self.start_endSpinner.setValue(4)
        self.start_endSpinner.setDecimals(4)

        self.first_stepsSpinner = QDoubleSpinBox()
        self.first_stepsSpinner.setRange(-999, 999)
        self.first_stepsSpinner.setValue(4)
        self.first_stepsSpinner.setDecimals(4)

        self.spinnerList.append([self.start_endSpinner, self.first_stepsSpinner])

        self.lay.addWidget(self.setValuesButton, 0, 4)
        self.lay.addWidget(self.startSpinner, 0, 0, 2,1)
        self.lay.addWidget(self.addButton, 0, 3)

        self.lay.addWidget(self.spinnerList[self.stepAreas - 1][0], 2, 0, 2,1)
        self.lay.addWidget(self.spinnerList[self.stepAreas - 1][1], 1, 1, 2,1)
        self.addButton.clicked.connect(self.addStepArea)
        self.setValuesButton.clicked.connect(self.setValues)

        paramList = self.getChangableParam()
        for i in range(len(paramList)):
            q_line_edit = QLineEdit()
            q_line_edit.setPlaceholderText("Enter List")
            self.widgetList.append([QComboBox(), q_line_edit])
            for j in paramList:
                self.widgetList[i][0].addItem(j)
                # self.widgetList[i].currentIndexChanged.connect(self.selectionchange)
        for i in range(len(self.widgetList)):
            self.lay.addWidget(self.widgetList[i][0], i+500, 0)
            self.lay.addWidget(self.widgetList[i][1], i+500, 1)




    def setValues(self):

        """
        
        makes Timescales-List and Step-List
        and emits them (connect is in the MainWindow)

        """

        valueList=[self.startSpinner.value()]
        stepList=[]
        for i in self.spinnerList:
            valueList.append(i[0].value())
            stepList.append(i[1].value())
        print(valueList, stepList)
        self.setTimeScale.emit(valueList, stepList)



    def addStepArea(self):
        self.stepAreas += 1

        s_eSpinner = QDoubleSpinBox()
        s_eSpinner.setRange(-999, 999)
        s_eSpinner.setValue(4)
        s_eSpinner.setDecimals(4)

        stepsSpinner = QDoubleSpinBox()
        stepsSpinner.setRange(-999, 999)
        stepsSpinner.setValue(4)
        stepsSpinner.setDecimals(4)



        self.spinnerList.append([s_eSpinner, stepsSpinner])
        self.lay.addWidget(self.spinnerList[self.stepAreas - 1][0], 2 * self.stepAreas + 4, 0, 2,1)
        self.lay.addWidget(self.spinnerList[self.stepAreas - 1][1], 2 * self.stepAreas + 3, 1, 2,1)

    def getChangableParam(self):
        return ["Temperature", "Param2", "Param3"]




if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    w = StackedExample()
    w.show()
    sys.exit(app.exec_())