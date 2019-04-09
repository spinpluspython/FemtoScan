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

from instruments.delaystage import DelayStage
from instruments.lockinamplifier import LockInAmplifier
from measurement.core import Experiment, Worker
from utilities.math import monotonically_increasing


class FastScan(Experiment):
    __TYPE = 'stepscan'

    def __init__(self, file=None, **kwargs):
        super().__init__(file=file, **kwargs)
        self.logger = logging.getLogger('{}.StepScan'.format(__name__))
        self.logger.info('Created instance of StepScan.')

        self.required_instruments = [LockInAmplifier, DelayStage]

        self.worker = FastScanWorker
        # define settings to pass to worker. these can be set as variables,
        # since they are class properties! see below...
        self.measurement_settings = {'averages': 2,
                                     'stage_positions': np.linspace(-1, 3, 10),
                                     'time_zero': -.5,
                                     }

    @property
    def stage_positions(self):
        return self.measurement_settings['stage_positions']

    @stage_positions.setter
    def stage_positions(self, array):
        if isinstance(array, list):
            array = np.array(array)
        assert isinstance(array, np.ndarray), 'must be a 1d array'
        assert len(array.shape) == 1, 'must be a 1d array'
        assert monotonically_increasing(array), 'array must be monotonically increasing'
        max_resolution = 0
        for i in range(len(array) - 1):
            step = array[i + 1] - array[i]
            if step < max_resolution:
                max_resolution = step
        self.logger.info('Stage positions changed: {} steps'.format(len(array)))
        self.logger.debug(
            'Current stage_positions configuration: {} steps from {} to {} with max resolution {}'.format(len(array),
                                                                                                          array[0],
                                                                                                          array[-1],
                                                                                                          max_resolution))

        self.measurement_settings['stage_positions'] = array

    @property
    def averages(self):
        return self.measurement_settings['averages']

    @averages.setter
    def averages(self, n):
        assert isinstance(n, int), 'cant run over non integer loops!'
        assert n > 0, 'cant run a negative number of loops!!'
        self.logger.info('Changed number of averages to {}'.format(n))
        self.measurement_settings['averages'] = n

    @property
    def time_zero(self):
        return self.measurement_settings['time_zero']

    @time_zero.setter
    def time_zero(self, t0):
        assert isinstance(t0, float) or isinstance(t0, int), 't0 must be a number!'
        self.logger.info('Changed time zero to {}'.format(t0))
        self.measurement_settings['time_zero'] = t0


class FastScanWorker(Worker):
    """ Subclass of Worker, designed to perform step scan measurements.

    Signals Emitted:

        finished (dict): at end of the scan, emits the results stored over the
            whole scan.
        newData (dict): emitted at each measurement point. Usually contains a
            dictionary with the last measured values toghether with scan
            current_step information.

    **Experiment Input required**:

    settings:
        stagePositions, lockinParametersToRead, dwelltime, numberOfScans
    instruments:
        lockin, stage

    """

    def __init__(self, file, base_instrument, parameters, **kwargs):
        super().__init__(file, base_instrument, parameters, **kwargs)
        self.logger = logging.getLogger('{}.Worker'.format(__name__))
        self.logger.debug('Created a "Worker" instance')

        self.check_requirements()
        self.single_measurement_steps = len(self.stage_positions) * self.averages
        self.parameters_to_measure = ['X', 'Y']
        self.logger.info('Initialized worker with single scan steps: {}'.format(self.single_measurement_steps))

    def check_requirements(self):
        assert hasattr(self, 'averages'), 'No number of averages was passed!'
        assert hasattr(self, 'stage_positions'), 'no values of the stage positions were passed!'
        assert hasattr(self, 'time_zero'), 'Need to tell where time zero is!'
        assert hasattr(self, 'lockin'), 'No Lockin Amplifier found: attribute name should be "lockin"'
        assert hasattr(self, 'delay_stage'), 'No stage found: attribute name should be "delay_stage"'

        self.logger.info('worker has all it needs. Ready to measure_avg!')

    def measure(self):
        """ Step Scan specific project procedure.

        Performs numberOfScans scans in which each moves the stage to the position defined in stagePositions, waits
        for the dwelltime, and finally records the values contained in lockinParameters from the Lock-in amplifier.
        """
        raise NotImplementedError('no Fast Scan measurement implemented.')


def main():
    pass


if __name__ == '__main__':
    main()
