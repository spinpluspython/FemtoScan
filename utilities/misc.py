# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson

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
import sys


def main():
    for i in iterate_ranges([[0, 2], [0, 3]]):
        print(i)


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

    operation(indexes, *args, **kwargs)
    while increments < operations:
        if indexes[pos] == ranges[pos][1] - 1:
            indexes[pos] = ranges[pos][0]
            pos -= 1
        else:
            indexes[pos] += 1
            increments += 1
            pos = len(ranges) - 1  # increment the innermost loop
            operation(indexes, *args, **kwargs)


def iterate_ranges(ranges):
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

    yield (indexes)
    while increments < operations:
        if indexes[pos] == ranges[pos][1] - 1:
            indexes[pos] = ranges[pos][0]
            pos -= 1
        else:
            indexes[pos] += 1
            increments += 1
            pos = len(ranges) - 1  # increment the innermost loop
            yield (indexes)


class TwoWayDict(dict):
    """dictionary which can be read as key: val or val: key."""

    def __setitem__(self, key, value):
        # Remove any previous connections with these values
        if key in self:
            del self[key]
        if value in self:
            del self[value]
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __delitem__(self, key):
        dict.__delitem__(self, self[key])
        dict.__delitem__(self, key)

    def __len__(self):
        """Returns the number of connections"""
        return dict.__len__(self) // 2


if __name__ == '__main__':
    main()
