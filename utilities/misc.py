# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
import sys


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


def main():
    pass


if __name__ == '__main__':
    main()
