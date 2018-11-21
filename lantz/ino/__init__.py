# -*- coding: utf-8 -*-
"""
    lantz.ino
    ~~~~~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    The lantz.ino package provides helper classes and methods to work with Arduino and
    a code generation utility.

    It builds on the idea of having a simple language for communication between Lantz and
    Arduino. In this way, it generates all the argument parsing code on the Arduino.

    Requires arduino-cli to be installed.

    See https://github.com/arduino/arduino-cli

    :copyright: 2018 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

from .base import INODriver

from .feat import (BoolFeat, BoolDictFeat,
                   QuantityFeat, QuantityDictFeat,
                   IntFeat, IntDictFeat)
