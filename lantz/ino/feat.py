# -*- coding: utf-8 -*-
"""
    lantz.ino.feat
    ~~~~~~~~~~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    The lantz.ino package provides helper classes and methods to work with Arduino.

    :copyright: 2018 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import collections

from lantz.core import mfeats

from .base import INOFeat, INODictFeat


class BoolFeat(INOFeat, mfeats.BoolFeat):

    INO_DATATYPE = 'B'

    def __init__(self, cmd, getter=True, setter=True):

        INOFeat.__init__(self, cmd)

        get_cmd = ('%s?' % cmd) if getter else None
        set_cmd = ('%s {}' % cmd) if setter else None

        mfeats.BoolFeat.__init__(self, get_cmd, set_cmd, '1', '0')

    def get_initial_value(self):
        # This is required because in Arduino a Bool is actually a string
        return '0'


class QuantityFeat(INOFeat, mfeats.QuantityFeat):

    INO_DATATYPE = 'F'

    def __init__(self, cmd, number_format='.2f', units=None, limits=None, getter=True, setter=True):

        INOFeat.__init__(self, cmd)

        get_cmd = ('%s?' % cmd) if getter else None
        set_cmd = ('%s {:%s}' % (cmd, number_format)) if setter else None

        mfeats.QuantityFeat.__init__(self, get_cmd, set_cmd, units=units, limits=limits)


class IntFeat(INOFeat, mfeats.IntFeat):

    INO_DATATYPE = 'I'

    def __init__(self, cmd, number_format='d', limits=None, getter=True, setter=True):

        INOFeat.__init__(self, cmd)

        get_cmd = ('%s?' % cmd) if getter else None
        set_cmd = ('%s {:%s}' % (cmd, number_format)) if setter else None

        mfeats.IntFeat.__init__(self, get_cmd, set_cmd, limits=limits)


class FloatFeat(INOFeat, mfeats.FloatFeat):

    INO_DATATYPE = 'F'

    def __init__(self, cmd, number_format='d', limits=None, getter=True, setter=True):

        INOFeat.__init__(self, cmd)

        get_cmd = ('%s?' % cmd) if getter else None
        set_cmd = ('%s {:%s}' % (cmd, number_format)) if setter else None

        mfeats.FloatFeat.__init__(self, get_cmd, set_cmd, limits=limits)


class BoolDictFeat(INODictFeat, mfeats.BoolDictFeat):

    INO_DATATYPE = 'B'

    def __init__(self, cmd, keys, getter=True, setter=True):

        INODictFeat.__init__(self, cmd, keys)

        get_cmd = ('%s? {key}' % cmd) if getter else None
        set_cmd = ('%s {key} {value}' % cmd) if setter else None

        mfeats.BoolDictFeat.__init__(self, get_cmd, set_cmd, '1', '0', keys=keys)

    def get_initial_value(self):
        # This is required because in Arduino a Bool is actually a string
        if self.keys:
            return {k: '0' for k in self.keys}
        return collections.defaultdict(lambda: '0')


class QuantityDictFeat(INODictFeat, mfeats.QuantityDictFeat):

    INO_DATATYPE = 'F'

    def __init__(self, cmd, keys, number_format='.2f', units=None, limits=None, getter=True, setter=True):

        INODictFeat.__init__(self, cmd, keys)

        get_cmd = ('%s? {key}' % cmd) if getter else None
        set_cmd = ('%s {key} {value:%s}' % (cmd, number_format)) if setter else None

        mfeats.QuantityDictFeat.__init__(self, get_cmd, set_cmd, units=units, limits=limits, keys=keys)


class IntDictFeat(INODictFeat, mfeats.IntDictFeat):

    INO_DATATYPE = 'I'

    def __init__(self, cmd, keys, number_format='d', limits=None, getter=True, setter=True):

        INODictFeat.__init__(self, cmd, keys)

        get_cmd = ('%s? {key}' % cmd) if getter else None
        set_cmd = ('%s {key} {value:%s}' % (cmd, number_format)) if setter else None

        mfeats.IntDictFeat.__init__(self, get_cmd, set_cmd, limits=limits, keys=keys)
