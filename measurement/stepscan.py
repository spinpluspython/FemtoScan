# -*- coding: utf-8 -*-
"""

@author: Vladimir Grigorev, Steinn Ymir Agustsson

    Copyright (C) 2018 Steinn Ymir Agustsson, Vladimir Grigorev

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

import time
import h5py
import pandas as pd
import numpy as np

from PyQt5 import QtCore

from measurement.core import Worker, Experiment
from instruments.lockinamplifier import LockInAmplifier, SR830
from instruments.delaystage import DelayStage
from utilities.misc import parse_setting

from utilities.qt import raise_Qerror


def main():
    import time
    from instruments.lockinamplifier import SR830, LockInAmplifier
    from instruments.delaystage import DelayStage
    from instruments.cryostat import Cryostat
    time.sleep(2)
    exp = StepScan()
    lockin = exp.add_instrument('lockin', LockInAmplifier())
    stage = exp.add_instrument('delay_stage', DelayStage())
    cryo = exp.add_instrument('cryo', Cryostat())
    exp.print_setup()
    time.sleep(1)
    exp.create_file()
    exp.add_parameter_iteration('temperature','K',cryo, 'change_temperature', [10,20])

    exp.start_measurement()


class StepScan(Experiment):
    # __verbose = parse_setting('general', 'verbose')
    __TYPE = 'stepscan'

    def __init__(self, file=None, **kwargs):
        super().__init__(file=file, **kwargs)
        self.required_instruments = [LockInAmplifier, DelayStage]

        self.worker = StepScanWorker
        self.measurement_settings = {'averages': 3,
                                     'stage_positions': [0,1,2,3],
                                     }



class StepScanWorker(Worker):
    """ Subclass of Worker, designed to perform step scan measurements.

    Signals Emitted:

    finished (dict): at end of the scan, emits the results stored over the whole scan.
    newData (dict): emitted at each measurement point. Usually contains a dictionary with the last measured values toghether with scan current_step information.

    **Experiment Input required**:

    settings:
        stagePositions, lockinParametersToRead, dwelltime, numberOfScans
    instruments:
        lockin, stage

    """

    def __init__(self, file, base_instrument, parameters, **kwargs):
        super().__init__(file, base_instrument, parameters, **kwargs)
        print('using Stepscan worker')
        self.check_requirements()
        self.single_measurement_steps = len(self.stage_positions) * self.averages
        self.parameters_to_measure = ['X', 'Y']
        print('single scan steps: {}'.format(self.single_measurement_steps))

    def check_requirements(self):
        assert hasattr(self, 'averages'), 'No number of averages was passed!'
        assert hasattr(self, 'stage_positions'), 'no values of the stage positions were passed!'
        assert hasattr(self, 'lockin'), 'No Lockin Amplifier found: attribute name should be "lockin"'
        assert hasattr(self, 'delay_stage'), 'No stage found: attribute name should be "delay_stage"'

        print('worker has all it needs. Ready to measure!')

    def measure(self):
        """ Step Scan specific work procedure.

        Performs numberOfScans scans in which each moves the stage to the position defined in stagePositions, waits
        for the dwelltime, and finally records the values contained in lockinParameters from the Lock-in amplifier.
        """
        print('\n---------------------\nNew measurement started\n---------------------')
        groupname = 'raw_data/'
        print(self.current_index)
        for i, idx in enumerate(self.current_index):
            groupname += str(self.values[i][idx]) + self.units[i] + ' - '
        groupname = groupname[:-3]
        with h5py.File(self.file, 'a') as f:
            f.create_group(groupname)

        for avg_n in range(self.averages):
            print('scanning average n {}'.format(avg_n))
            d_avg = {}
            df_name = groupname + '/avg{}'.format(str(avg_n).zfill(4))
            for i, pos in enumerate(self.stage_positions):
                self.delay_stage.move_absolute(pos)
                # real_pos = self.delay_stage.position.get()  # TODO: implement, or remove
                time.sleep(self.lockin.dwelltime)
                result = self.lockin.read_snap(self.parameters_to_measure, format='dict')  # TODO: implement data management!
                result['pos'] = pos
                for k, v in result.items():
                    try:
                        d_avg[k].append(v)
                    except:
                        d_avg[k] = [v]
                self.newData.emit()
                self.increment_progress_counter()
                print('current_step: {:.3f}% step {} of {}'.format(self.progress,self.current_step,self.n_of_steps))
            df = pd.DataFrame(data=d_avg, columns=self.parameters_to_measure, index=d_avg['pos'])
            df.to_hdf(self.file, 'raw_data/' + df_name, mode='a', format='fixed')

if __name__ == '__main__':
    import os, sys

    if os.getcwd()[-9] != 'FemtoScan':
        os.chdir('../')
    from utilities.misc import my_exception_hook
    # used to see errors generated by PyQt5 in pycharm:
    sys._excepthook = sys.excepthook
    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook
    main()
