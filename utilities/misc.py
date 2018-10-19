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


def nested_for(ranges, operation, *args, **kwargs):
    """this is some magic iteration script. it creates a nested for loop
    :parameters:
        ranges: tuple of tuples
            define the ranges of the loops. each tuple creates a loop with range(tuple[0],tuple[1])
        operation:
            the operation to be performed
        *args:
            passed to operation
        **kwargs:
            passed to operation
    """
    from operator import mul
    from functools import reduce
    operations = reduce(mul, (p[1] - p[0] for p in ranges)) - 1
    indexes = [i[0] for i in ranges]
    pos = len(ranges) - 1
    increments = 0

    operation(indexes,*args, **kwargs)
    while increments < operations:
        if indexes[pos] == ranges[pos][1] - 1:
            indexes[pos] = ranges[pos][0]
            pos -= 1
        else:
            indexes[pos] += 1
            increments += 1
            pos = len(ranges) - 1  # increment the innermost loop
            operation(indexes,*args, **kwargs)

def main():
    pass


if __name__ == '__main__':
    main()
