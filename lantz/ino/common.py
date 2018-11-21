# -*- coding: utf-8 -*-
"""
    lantz.ino.common
    ~~~~~~~~~~~~~~~~

    Common functions and definitions.

    The lantz.ino package provides helper classes and methods to work with Arduino.

    :copyright: 2018 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

from collections import namedtuple
import os
import pickle

import yaml


def write_user_timestamp(folder):
    hfile = os.path.join(folder, 'inodriver_user.h')
    cppfile = os.path.join(folder, 'inodriver_user.cpp')

    hfile_ts = os.path.getmtime(hfile)
    cppfile_ts = os.path.getmtime(cppfile)

    with open(os.path.join('.ts.pickle'), 'wb') as fo:
        pickle.dump((hfile_ts, cppfile_ts), fo)


def read_user_timestamp(folder):
    hfile = os.path.join(folder, 'inodriver_user.h')
    cppfile = os.path.join(folder, 'inodriver_user.cpp')

    hfile_ts = os.path.getmtime(hfile)
    cppfile_ts = os.path.getmtime(cppfile)

    try:
        with open(os.path.join('.ts.pickle'), 'rb') as fi:
            return pickle.load(fi), (hfile_ts, cppfile_ts)
    except FileNotFoundError:
        return (None, None), (hfile_ts, cppfile_ts)


def user_local_matches_remote(sketch_folder):
    last, current = read_user_timestamp(sketch_folder)
    return last == current


class Packfile(namedtuple('Packfile', 'sketch_folder class_spec fqbn port usbID')):

    @classmethod
    def from_defaults(cls, sketch_folder, class_spec):
        return cls(sketch_folder, class_spec, '', '', '')

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r', encoding='utf-8') as fi:
            data = yaml.load(fi)

        return cls(*map(data.get, cls._fields))

    def to_file(self, filename):
        with open(filename, mode='w', encoding='utf-8') as fo:
            yaml.dump(dict(self._asdict()), fo, default_flow_style=False)

