
import argparse
from datetime import datetime
import importlib
import inspect
import os
import subprocess
import sys

from lantz import ArgumentParserSC
from . import arduinocli, common
from .base import hasher

def main(args=None):
    """Run simulators.
    """

    sys.path.insert(0, os.getcwd())

    parser = ArgumentParserSC('command', CHOICES, description='Arduino-Lantz bridge helper')
    parser.dispatch(args)


def info(args=None):

    parser = argparse.ArgumentParser(description='Print information of a project')
    parser.add_argument('packfile', help='Path of the pack file.', type=common.Packfile.from_file)

    args = parser.parse_args(args)

    last, current = common.read_user_timestamp(args.packfile.sketch_folder)
    print('Upload timestamp (.h, .cpp): %s, %s' % last)
    print('Current timestamp (.h, .cpp): %s, %s' % current)
    print('')


def refresh(args=None):

    parser = argparse.ArgumentParser(description='Refresh installation and dependenceis')
    args = parser.parse_args(args)

    out = subprocess.run(['arduino-cli', 'core', 'update-index'])

    out = subprocess.run(['arduino-cli', 'core', 'search', 'list'])
    print('You might need to install extra tools for your board:\n'
          '     https://github.com/arduino/arduino-cli')

    out = subprocess.run(['arduino-cli', 'lib', 'update-index'])


def new(args=None):

    parser = argparse.ArgumentParser(description='Generate new Arduino-Lant bridge')
    parser.add_argument('class_spec')
    parser.add_argument('base_folder', nargs='?', default='.')
    parser.add_argument('-f', '--force', help='Force overwriting user file.', action='store_true')
    args = parser.parse_args(args)

    cls = _load_class(args.class_spec)

    base = args.class_spec.split(':')[1]

    packfile = os.path.join(args.base_folder, base) + '.pack.yaml'
    skfolder = os.path.abspath(os.path.join(args.base_folder, base))

    pf = common.Packfile.from_defaults(skfolder, args.class_spec)

    if not args.force:
        if os.path.exists(skfolder):
            sys.exit('Already exists: %s\n Use -f (--force) to overwrite.' % skfolder)

    os.makedirs(skfolder, exist_ok=True)

    _subgenerate(cls, skfolder, args.force)

    from .templates import ino, serialcommand, HEADER_DONOT

    pf.to_file(packfile)

    with open(os.path.join(skfolder, base + '.ino'), mode='w', encoding='utf-8') as fo:
        fo.write(HEADER_DONOT.format(filename=inspect.getfile(cls),
                                     klass=cls.__qualname__,
                                     timestamp=datetime.now().isoformat(),
                                     hash=hasher(cls)))
        fo.write(ino.CPP)

    with open(os.path.join(skfolder, 'SerialCommand.cpp'), mode='w', encoding='utf-8') as fo:
        fo.write(serialcommand.CPP)

    with open(os.path.join(skfolder, 'SerialCommand.h'), mode='w', encoding='utf-8') as fo:
        fo.write(serialcommand.H)

    print('Packfile created in: %s' % packfile)
    print('Sketch created in: %s' % skfolder)


def generate(args=None):

    parser = argparse.ArgumentParser(description='Regenerate code for project.')
    parser.add_argument('packfile', help='Path of the pack file.', type=common.Packfile.from_file)
    parser.add_argument('-f', '--force', help='Force overwriting user file.', action='store_true')
    args = parser.parse_args(args)

    try:
        _generate(args.packfile, args.force)
    except FileExistsError:
        print('inodriver_user.h and inodriver_user.cpp are present in the destination folder. '
              'Use -f (--force) ')


def update(args=None):

    parser = argparse.ArgumentParser(description='Compile and upload')
    parser.add_argument('packfile', help='Path of the pack file.', type=common.Packfile.from_file)
    parser.add_argument('-n', '--do-not-upload', help='Compile and upload project.', action='store_true')
    parser.add_argument('-f', '--force', help='Force compilation and upload even if the USER project has not changed.', action='store_true')
    args = parser.parse_args(args)

    try:
        arduinocli.check_cli()
    except arduinocli.ArduinoCliNotFound as e:
        sys.exit(str(e))

    try:
        arduinocli.compile_and_upload(args.packfile, not args.do_not_upload, args.force)
    except arduinocli.NoUpdateNeeded:
        print('No update needed. Use -f (--force) to do it anyway.')
    except ValueError as e:
        sys.exit(str(e))


def _generate(packfile, overwrite_user=False):

    _subgenerate(_load_class(packfile.class_spec), packfile.sketch_folder, overwrite_user)


def _load_class(class_spec):

    module_spec, klass_name = class_spec.split(':')

    module = importlib.import_module(module_spec)
    my_class = getattr(module, klass_name)

    from .base import INODriver

    if not issubclass(my_class, INODriver):
        raise ValueError('%s is not a subclass of INODriver')

    return my_class


def _subgenerate(cls, skfolder, overwrite_user=False):

    cls.ino_bridge_write(skfolder)
    cls.ino_user_write(skfolder, overwrite_user)


CHOICES = {'refresh': refresh,
           'new': new,
           'info': info,
           'generate': generate,
           'update': update,
           }

try:
    def testpanel(args=None):
        """Run simulators.
        """

        parser = argparse.ArgumentParser(description='Open a testpanel. Requires lantz.qt')
        parser.add_argument('packfile', help='Path of the pack file.', type=common.Packfile.from_file)

        args = parser.parse_args(args)

        from lantz.qt.utils.qt import QtGui

        klass = _load_class(args.packfile.class_spec)

        from lantz.qt import start_test_app, wrap_driver_cls

        from lantz.core.log import log_to_screen, DEBUG

        log_to_screen(DEBUG)

        Qklass = wrap_driver_cls(klass)
        with Qklass.via_packfile(args.packfile, check_update=True) as inst:
            start_test_app(inst)

    CHOICES['testpanel'] = testpanel

except ImportError:
    pass

if __name__ == '__main__':
    main()
