# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
import time
from PyQt5 import QtCore

from measurement.core import Worker, Experiment
from instruments.lockinamplifier import LockInAmplifier, SR830
from instruments.delaystage import DelayStage

from utilities.qt import raise_Qerror


def main():
    stepscan = StepScan()
    stepscan.add_instrument('lockin', SR830())
    stepscan.add_instrument('stage', DelayStage())
    stepscan.check_requirements()
    pass


class StepScan(Experiment):
    __TYPE = 'stepscan'

    def __init__(self, file=None, **kwargs):
        super().__init__(file=file, **kwargs)
        self.required_instruments = [LockInAmplifier, DelayStage]

        self.worker = StepScanWorker
        self.scan_settings = {'averages': 10,
                              'stage_positions': [],
                              }

    def initialize_experiment(self):
        """ set up all what is needed for a measurement session.

        - check if parameter iteration methods, and relative values are present
        - check if the file name chosen is already present, otherwise append number
        - write file structure in the h5 file chosen
        - preallocate data file structures
        - disconnect all devices
        """

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

    def __init__(self, file, base_instrument, parameters, **kwargs):
        super().__init__(file, base_instrument, parameters, **kwargs)
        self.__single_measurement_steps = len(self.stage_positions) * self.averages

    def check_requirements(self):
        assert hasattr(self, 'averages'), 'No number of averages was passed!'
        assert hasattr(self, 'stage_positions'), 'no values of the stage positions were passed!'
        assert hasattr(self, 'lockin')
        assert hasattr(self, 'delay_stage')

        print('worker has all it needs. Ready to measure!')

    def measure(self):
        """ Step Scan specific work procedure.

        Performs numberOfScans scans in which each moves the stage to the position defined in stagePositions, waits
        for the dwelltime, and finally records the values contained in lockinParameters from the Lock-in amplifier.
        """

        for avg_n in range(self.averages):
            print('scanning average n {}'.format(avg_n))

            for i, pos in enumerate(self.stage_positions):
                self.delay_stage.move_to(pos)
                real_pos = self.delay_stage.position.get()  # TODO: implement, or remove
                time.sleep(self.lockin.dwelltime)
                data = self.lockin.readSnap(['X', 'Y'])  # TODO: implement data management!
                self.newData.emit(data)
                self.increment_progress_counter()


if __name__ == '__main__':
    import os

    if os.getcwd()[-9] != 'FemtoScan':
        os.chdir('../')
    main()
