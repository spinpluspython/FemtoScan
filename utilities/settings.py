# -*- coding: utf-8 -*-
"""

@author: Steinn Ymir Agustsson
"""
import ast
import os
from configparser import ConfigParser

def make_settings():
    settings_dict = {'paths':{'h5_data':'D:\data',
                              },
                     'general':{'verbose':'True',
                                },
                     'launcher':{'mode':'cmd',
                                 'recompile':'False',
                                 }
                     }

    settings = ConfigParser()
    for section_name, section in settings_dict.items():
        settings.add_section(section_name)
        for key, val in section.items():
            settings.set(section_name, key, str(val))

    with open('SETTINGS.ini', 'w') as configfile:
        settings.write(configfile)


def parse_setting(category, name, settings_file='default'):
    """ parse setting file and return desired value

    Args:
        category (str): title of the category
        name (str): name of the parameter
        setting_file (str): path to setting file. If set to 'default' it takes
            a file called SETTINGS.ini in the main folder of the repo.

    Returns:
        value of the parameter, None if parameter cannot be found.
    """
    settings = ConfigParser()
    if settings_file == 'default':
        current_path = os.path.dirname(__file__)
        while not os.path.isfile(os.path.join(current_path, 'SETTINGS.ini')):
            current_path = os.path.split(current_path)[0]

        settings_file = os.path.join(current_path, 'SETTINGS.ini')
    settings.read(settings_file)

    try:
        value = settings[category][name]
        return ast.literal_eval(value)
    except KeyError:
        print('No entry "{}" in category "{}" found in SETTINGS.ini'.format(name, category))
        return None
    except:
        return(value)
