# -*- coding: utf-8 -*-
"""
    lantz.ino.base
    ~~~~~~~~~~~~~~

    Provides base classes for Arduino related Lantz Drivers, Feats and DictFeats.

    The lantz.ino package provides helper classes and methods to work with Arduino.

    :copyright: 2018 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

from collections import ChainMap
from datetime import datetime
import hashlib
import inspect
import os
import pickle
import time

from lantz.core import MessageBasedDriver, Feat, log

from . import common, arduinocli
from .templates import bridge, ino, user, HEADER_DO, HEADER_DONOT

DESCRIPTION = {
    'B': 'bool as string: True as "1", False as "0"',
    'I': 'int as string',
    'F': 'float as string',
}

CONVERSION = {
    'B': ('int', 'atoi', '0'),
    'I': ('int', 'atoi', '0'),
    'F': ('float', 'atof', '0.0'),
}

ARG = """
  arg = sCmd.next();
  if (arg == NULL) {
    error("No value stated");
    return;
  }
  %s %s = %s(arg);
"""

FEAT_HEADER = """
  // %s
  // <%s> %s 
"""

FEAT_GETTER = """
  // Getter:
  //   %s? 
  // Returns: <%s> 
  %s("%s?", wrapperGet_%s); 
"""

FEAT_SETTER = """
  // Setter:
  //   %s <%s> 
  // Returns: OK or ERROR    
  %s("%s", wrapperSet_%s); 
"""

FEAT_WRAPPER_GETTER = """
void wrapperGet_%s() { 
  Serial.println(get_%s()); 
}; 

"""

FEAT_WRAPPER_SETTER = """
void wrapperSet_%s() {
  char *arg;
  %s
  int err = set_%s(value);
  if (err == 0) {
    ok();
  } else {
    error_i(err);
  }
};

"""

DICTFEAT_HEADER = """
  // %s
  // <%s> %s 
  // <%s> %s 
"""

DICTFEAT_GETTER = """
  // Getter:
  //   %s? <%s>
  // Returns: <%s> 
  %s("%s?", wrapperGet_%s); 
"""

DICTFEAT_SETTER = """
  // Setter:
  //   %s <%s> <%s>
  // Returns: OK or ERROR    
  %s("%s", wrapperSet_%s); 
"""

DICTFEAT_WRAPPER_GETTER = """
void wrapperGet_%s() { 
  char *arg;
  %s

  Serial.println(get_%s(key)); 
}; 

"""

DICTFEAT_WRAPPER_SETTER = """
void wrapperSet_%s() {
  char *arg;
  %s
  %s
  
  int err = set_%s(key, value);
  if (err == 0) {
    ok();
  } else {
    error_i(err);
  }
};

"""


def _write_feat_setup(fcpp, name, cmd, datatype, fget, fset, register='sCmd.addCommand'):
    fcpp.write(FEAT_HEADER % (name, datatype, DESCRIPTION[datatype]))

    if fget:
        fcpp.write(FEAT_GETTER % (cmd, datatype, register, cmd, cmd))

    if fset:
        fcpp.write(FEAT_SETTER % (cmd, datatype, register, cmd, cmd))


def _write_feat_wrapper(fh, fcpp, cmd, datatype, fget, fset):

    t, fun, default = CONVERSION[datatype]

    if fget:
        fcpp.write(FEAT_WRAPPER_GETTER % (cmd, cmd))
        fh.write('void wrapperGet_%s(); \n' % cmd)

    if fset:
        fcpp.write(FEAT_WRAPPER_SETTER % (cmd, ARG % (t, 'value', fun),  cmd))
        fh.write('void wrapperSet_%s(); \n' % cmd)


def _write_feat_wrapped(fh, fcpp, cmd, datatype, fget, fset):

    t, fun, default = CONVERSION[datatype]

    if fget:
        fcpp.write('%s get_%s() {\n  return %s;\n};\n\n' % (t, cmd, default))
        fh.write('%s get_%s(); \n' % (t, cmd))

    if fset:
        fcpp.write('int set_%s(%s value) {\n  return 0;\n};\n\n' % (cmd, t))
        fh.write('int set_%s(%s); \n' % (cmd, t))


def _write_dictfeat_setup(fcpp, name, cmd, datatype, key_datatype, fget, fset, register='sCmd.addCommand'):

    fcpp.write(DICTFEAT_HEADER % (name, datatype, DESCRIPTION[datatype], key_datatype, DESCRIPTION[key_datatype]))

    if fget:
        fcpp.write(DICTFEAT_GETTER % (cmd, key_datatype, datatype, register, cmd, cmd))

    if fset:
        fcpp.write(DICTFEAT_SETTER % (cmd, key_datatype, datatype, register, cmd, cmd))


def _write_dictfeat_wrapper(fh, fcpp, cmd, datatype, key_datatype, fget, fset):

    t, fun, default = CONVERSION[datatype]
    kt, kfun, kdefault = CONVERSION[key_datatype]

    if fget:
        fcpp.write(DICTFEAT_WRAPPER_GETTER % (cmd, ARG % (kt, 'key', kfun), cmd))
        fh.write('void wrapperGet_%s(); \n' % cmd)

    if fset:
        fcpp.write(DICTFEAT_WRAPPER_SETTER % (cmd, ARG % (kt, 'key', kfun), ARG % (t, 'value', fun), cmd))
        fh.write('void wrapperSet_%s(); \n' % cmd)


def _write_dictfeat_wrapped(fh, fcpp, cmd, datatype, key_datatype, fget, fset):

    t, fun, default = CONVERSION[datatype]
    kt, kfun, kdefault = CONVERSION[key_datatype]

    if fget:
        fcpp.write('%s get_%s(%s key) {\n  return %s;\n};\n\n' % (t, cmd, kt, default))
        fh.write('%s get_%s(%s); \n' % (t, cmd, kt))

    if fset:
        fcpp.write('int set_%s(%s key, %s value) {\n  return 0;\n};\n\n' % (cmd, kt, t))
        fh.write('int set_%s(%s, %s); \n' % (cmd, kt, t))


def hasher(obj):
    return hashlib.sha1(pickle.dumps(obj)).hexdigest()


class INODriver(MessageBasedDriver):

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\r\n'},
                'ASRL': {'baud_rate': 9600},
                }


    @classmethod
    def via_packfile(cls, path_or_packfile, check_update=False, name=None, **kwargs):

        if isinstance(path_or_packfile, common.Packfile):
            pf = path_or_packfile
        else:
            pf = common.Packfile.from_file(path_or_packfile)

        if check_update:
            try:
                arduinocli.compile_and_upload(pf, upload=True)
            except arduinocli.NoUpdateNeeded:
                print('No update needed')

        if not pf.port:
            boards = arduinocli.find_boards_pack(pf)
            pf = arduinocli.just_one(pf, boards)
        return cls.via_serial(pf.port, name=name, **kwargs)

    def initialize(self):
        super().initialize()
        # Some Arduino reset the Serial upon establishing connection (after opening the port)
        # This sleep is required to avoid sending messages when the board is not ready.
        time.sleep(3)

    @Feat(read_once=True)
    def idn(self):
        """Instrument identification.
        """
        return self.parse_query('INFO?',
                                format='{klass:s},{compile_datetime:s}')

    def read(self, termination=None, encoding=None):
        line = super().read()
        parts = line.split('#')

        for part in parts[:-1]:
            self.log_debug(part.decode('utf-8'))

        return parts[-1]

    @classmethod
    def ino_bridge_write(cls, folder):

        os.makedirs(folder, exist_ok=True)

        hfile = os.path.join(folder, 'inodriver_bridge.h')
        cppfile = os.path.join(folder, 'inodriver_bridge.cpp')

        with open(cppfile, 'w', encoding='UTF-8') as fcpp, \
            open(hfile, 'w', encoding='UTF-8') as fh:

            header = HEADER_DONOT.format(filename=inspect.getfile(cls),
                                         klass=cls.__qualname__,
                                         timestamp=datetime.now().isoformat(),
                                         hash=hasher(cls))

            fh.write(header)
            fh.write('#ifndef inodriver_bridge_h\n'
                     '#define inodriver_bridge_h\n')

            fcpp.write(header)

            fh.write(bridge.IN_H_HEADER)
            fcpp.write(bridge.IN_CPP_HEADER)

            fh.write('void bridge_setup();')
            fcpp.write('void bridge_setup() {')

            fcpp.write(bridge.IN_SETUP)

            cm = ChainMap(cls._lantz_feats, cls._lantz_dictfeats)

            for feat_name, feat in cm.items():
                if isinstance(feat, INOFeat):
                    feat.ino_write_setup(fcpp)

            fcpp.write('}')

            fh.write(bridge.IN_H_BODY)
            fcpp.write(bridge.IN_CPP_BODY % cls.__qualname__)

            for feat_name, feat in cm.items():
                if isinstance(feat, INOFeat):
                    fcpp.write('// COMMAND: %s, FEAT: %s\n' % (feat.ino_cmd, feat.name))
                    feat.ino_write_wrapper(fh, fcpp)
                    fcpp.write('\n\n')

            fh.write('\n\n#endif // inodriver_bridge_h')

    @classmethod
    def ino_user_write(cls, folder, overwrite=False):

        os.makedirs(folder, exist_ok=True)

        hfile = os.path.join(folder, 'inodriver_user.h')
        cppfile = os.path.join(folder, 'inodriver_user.cpp')

        if not overwrite:
            if os.path.exists(hfile) or os.path.exists(cppfile):
                raise FileExistsError

        with open(cppfile, 'w', encoding='UTF-8') as fcpp, \
            open(hfile, 'w', encoding='UTF-8') as fh:

            header = HEADER_DO.format(filename=inspect.getfile(cls),
                                      klass=cls.__qualname__,
                                      timestamp=datetime.now().isoformat(),
                                      hash=hasher(cls))

            fh.write(header)
            fh.write('#ifndef inodriver_user_h\n'
                     '#define inodriver_user_h\n')

            fcpp.write(header)

            fh.write(user.H)
            fcpp.write(user.CPP)
            cm = ChainMap(cls._lantz_feats, cls._lantz_dictfeats)

            for feat_name, feat in cm.items():
                if isinstance(feat, INOFeat):
                    fcpp.write('// COMMAND: %s, FEAT: %s\n' % (feat.ino_cmd, feat.name))
                    feat.ino_write_wrapped(fh, fcpp)
                    fcpp.write('\n')

            fh.write('\n\n#endif // inodriver_user_h')


class INOFeat:

    INO_DATATYPE = None

    def __init__(self, ino_cmd):
        if not ino_cmd.isidentifier():
            raise ValueError("'%s' is not a valid command.\n(Just letters and underscores. "
                             "Numbers are allowed but not at the beginning)")

        self.ino_cmd = ino_cmd

    def ino_write_setup(self, fo):
        _write_feat_setup(fo, self.name, self.ino_cmd, self.INO_DATATYPE, self.fget, self.fset)

    def ino_write_wrapper(self, fh, fo):
        _write_feat_wrapper(fh, fo, self.ino_cmd, self.INO_DATATYPE, self.fget, self.fset)

    def ino_write_wrapped(self, fh, fo):
        _write_feat_wrapped(fh, fo, self.ino_cmd, self.INO_DATATYPE, self.fget, self.fset)


class INODictFeat(INOFeat):

    INO_DATATYPE = None

    INO_KEY_DATATYPE = None

    def __init__(self, ino_cmd, keys):
        INOFeat.__init__(self, ino_cmd)

        types = set(map(type, keys))

        if len(types) != 1:
            raise ValueError('All keys must be of the same type (not %r)' % types)

        ty = types.pop()

        if ty is int:
            self.INO_KEY_DATATYPE = 'I'
        elif ty is float:
            self.INO_KEY_DATATYPE = 'F'
        elif ty is bool:
            self.INO_KEY_DATATYPE = 'B'
        elif ty is str:
            self.INO_KEY_DATATYPE = 'S'
        else:
            raise ValueError('Cannot handle keys of type %s' % ty)

    def ino_write_setup(self, fo):
        _write_dictfeat_setup(fo, self.name, self.ino_cmd, self.INO_DATATYPE, self.INO_KEY_DATATYPE, self.fget, self.fset)

    def ino_write_wrapper(self, fh, fo):
        _write_dictfeat_wrapper(fh, fo, self.ino_cmd, self.INO_DATATYPE, self.INO_KEY_DATATYPE, self.fget, self.fset)

    def ino_write_wrapped(self, fh, fo):
        _write_dictfeat_wrapped(fh, fo, self.ino_cmd, self.INO_DATATYPE, self.INO_KEY_DATATYPE, self.fget, self.fset)
