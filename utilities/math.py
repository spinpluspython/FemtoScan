# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
import numpy as np


def monotonically_increasing(l):
    return all(x < y for x, y in zip(l, l[1:]))


def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


def globalcounter(idx,M):
    counterlist = idx[::-1]
    for i in range(len(counterlist)):
        counterlist[i] = counterlist[i]*np.prod(M[:i])
    return int(np.sum(counterlist))


def main():
    pass


if __name__ == '__main__':
    main()
