# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
Modified from "snomtools" by Michael Hartlet
"""
# __author__ = 'hartelt'

"""
This file provides the central unit registry that should be used in all scripts that use snomtools.
This avoids errors between quantities of different unit registries that occur when using multiple imports.
Custom units and prefixes that we use frequently should be defined here to get consistency.
"""

# Import pint and initialize a standard unit registry:
import pint
import pint.quantity
import numpy

ureg = pint.UnitRegistry()
Quantity = ureg.Quantity

# Custom units that we use frequently can be defined here:
# ureg.define('dog_year = 52 * day = dy')
ureg.define('pixel = []')
ureg.define('count = []')

# Custom prefixes we use frequently can be defined here:
# ureg.define('myprefix- = 30 = my-')

# Custom contexts we use frequently can be defined here:
c = pint.Context('light')
c.add_transformation('[length]', '[time]', lambda ureg, x: x / ureg.speed_of_light)
c.add_transformation('[time]', '[length]', lambda ureg, x: x * ureg.speed_of_light)
ureg.add_context(c)



def main():
    pass


if __name__ == '__main__':
    main()