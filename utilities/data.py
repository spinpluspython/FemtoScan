# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
import h5py
import numpy as np


def dict_to_hdf(f, group, data_dict, columns, index):
    """ writes a dictionary to an h5 group

    It creates a group inside the given group of the given file, with name dname.
    There it creates 3 datasets:
        - data: containing an array, ordered by columns of the data contained in
            each 1d array found in a key of the data_dict
        - columns: list of names of the columns to save. It searches in the dictionary
            for these as keys and grabs the data from these. Other keys are ignored
        - index: the 'x' axis, or index of the datasets passed.

    #todo: need asserts, better generalization and a lot more.

    Args:
        f (hdf5 file or str): hdf5 file handle, or string to the file name
        group (str): group name where to save data
        dname: name of the dataset/datagroup created
        data: data to be written
        columns: column labels
        index: row labels

    """
    close = False
    if isinstance(f, h5py._hl.files.File):
        f = f
    elif isinstance(f, str):
        close = True
        f = h5py.File(f, 'a')


    data_array = np.zeros((len(data_dict[columns[0]]),len(columns)))
    for i, col in enumerate(columns):
        data_array[:,i] = data_dict[col]

    cols_str_array = [np.string_(x) for x in columns]


    f.create_dataset('/'+group+'/data',data=data_array)
    f.create_dataset('/'+group+'/index', data=index)
    f.create_dataset('/'+group+'/columns', data=cols_str_array)


    if close:
        f.close()





def main():
    pass


if __name__ == '__main__':
    main()
