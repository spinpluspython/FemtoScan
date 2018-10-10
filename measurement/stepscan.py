# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
from PyQt5 import QtCore
from measurement.workers import Worker
from utils.utils import raise_Qerror
import time

def main():
    pass


class StepScanWorker(Worker):
    """ Subclass of Worker, designed to perform step scan measurements.

    Signals Emitted:

    finished (dict): at end of the scan, emits the results stored over the whole scan.
    newData (dict): emitted at each measurement point. Usually contains a dictionary with the last measured values toghether with scan progress information.

    **Experiment Input required**:

    settings:
        stagePositions, lockinParametersToRead, dwelltime, numberOfScans
    instruments:
        lockin, stage

    """

    def __init__(self, settings, instruments):
        super(StepScanWorker, self).__init__(settings, instruments)

        self.state = 'loading'

        self.requiredSettings = ['stagePositions', 'lockinParametersToRead', 'dwelltime', 'numberOfScans']
        self.requiredInstruments = ['lockin', 'stage']

        self.state = 'connecting instruments'
        self.initialize_instruments()
        #
        # for instrument, value in instruments.items():
        #     inst_string = str(instrument).lower().replace('-','')
        #     setattr(self, inst_string, value)
        # for setting, value in settings.items():
        #     inst_string = str(instrument).lower().replace('-','')
        #     setattr(self, inst_string, value)

        self.state = 'idle'

    def work(self):
        """ Step Scan specific work procedure.

        Performs numberOfScans scans in which each moves the stage to the position defined in stagePositions, waits
        for the dwelltime, and finally records the values contained in lockinParameters from the Lock-in amplifier.
        """
        print('worker scanning')
        self.state = 'scanning'
        pointsPerScan = len(self.stagePositions)
        j=0
        while j < self.numberOfScans:
            j=j+1
            self.result['data'][j] = {}
            for i in range(pointsPerScan):
                pos = self.stagePositions[i]
                self.stage.moveTo(pos)  # move stage to new position
                time.sleep(self.dwelltime)  # wait for the lock-in value to saturate
                # read data and add scan status information to the output dictionary.
                newDataDict = self.lockin.readSnap(self.lockinParametersToRead)
                # TODO: implement stage position readout
                newDataDict['stagePosition'] = pos
                # append data to results dataset
                for key, val in newDataDict.items():
                    self.result['data'][j][key] = val
                # add lables for scan number (j) and point (i) for data emission only.
                newDataDict['point'] = i
                newDataDict['scanNumber'] = j  # add lable for scan number in order to track it in emitted signal
                newDataDict['scanProgress'] = i / pointsPerScan
                newDataDict['totalProgress'] = (i + j * pointsPerScan) / (self.numberOfScans * pointsPerScan)
                self.newData.emit(newDataDict)

                if self.shouldStop:
                    self.kill_worker()

        self.finished.emit(self.result)
        self.state = 'complete'

    @QtCore.pyqtSlot(int)
    def set_number_of_scans(self, new_numberOfScans):
        self.set_numberOfScans = new_numberOfScans

if __name__ == '__main__':
    main()