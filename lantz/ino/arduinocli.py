# -*- coding: utf-8 -*-
"""
    lantz.ino.arduinocli
    ~~~~~~~~~~~~~~~~~~~~

    Convenience functions to call the arduino-cli

    See: https://github.com/arduino/arduino-cli

    The lantz.ino package provides helper classes and methods to work with Arduino.

    :copyright: 2018 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import json
import subprocess

from . import common


class NoUpdateNeeded(Exception):
    pass


class ArduinoCliNotFound(Exception):

    def __str__(self):
        return ('The arduino-cli is required for this feature.\n'
                'Please install it following the instructions here:\n'
                '    https://github.com/arduino/arduino-cli\n')


def check_cli():

    try:
        out = run_arduino_cli('version')
    except FileNotFoundError:
        raise ArduinoCliNotFound


def run_arduino_cli(args):

    out = subprocess.run(['arduino-cli', '--format', 'json'] + args.split(' '), stdout=subprocess.PIPE)

    return json.loads(out.stdout)


def find_boards(board, port, board_id):
    boards = run_arduino_cli('board list')

    # {'serialBoards': [{'name': 'Arduino/Genuino Uno', 'fqbn': 'arduino:avr:uno',
    # 'port': '/dev/cu.usbmodem14111', 'usbID': '2341:0043 - 956323133343513072D1'}], 'networkBoards': []}
    found = []

    for b in boards.get('serialBoards', []):
        if board and not b['fqbn'] == board:
            continue
        if port and not b['port'] == port:
            continue
        if board_id and not b['usbID'].split.startswith(board_id):
            continue

        found.append(b)

    for b in boards['networkBoards']:
        pass

    return found


def find_boards_pack(packfile):
    boards = find_boards(packfile.fqbn, packfile.port, packfile.usbID)

    out = []
    for b in boards:
        out.append(packfile._replace(fqbn=b['fqbn'], usbID=b['usbID'], port=b['port']))

    return out


def just_one(pf, boards):

    if len(boards) > 1:
        raise ValueError(
            'Too many matching boards for board=%s, port=%s, board_id=%s' % (pf.fqbn, pf.port, pf.usbID))
    elif len(boards) == 0:
        raise ValueError(
            'No many matching boards for board=%s, port=%s, board_id=%s' % (pf.fqbn, pf.port, pf.usbID))

    return boards[0]


def compile_and_upload(packfile, upload=False, force=False):

    if not force:
        if common.user_local_matches_remote(packfile.sketch_folder):
            raise NoUpdateNeeded

    if not packfile.port or not packfile.fqbn:
        boards = find_boards_pack(packfile)

    if not packfile.fqbn:
        packfile = just_one(packfile, boards)
        print('Found board=%s, port=%s, board_id=%s' % (packfile.fqbn, packfile.port, packfile.usbID))

    out = subprocess.run(['arduino-cli', 'compile', '-b', packfile.fqbn, packfile.sketch_folder])

    if upload:

        if not packfile.port:
            packfile = just_one(packfile, boards)
            print('Found board=%s, port=%s, board_id=%s' % (packfile.fqbn, packfile.port, packfile.usbID))

        out = subprocess.run(['arduino-cli', 'upload', '-b', packfile.fqbn, '-p', packfile.port, packfile.sketch_folder])

        common.write_user_timestamp(packfile.sketch_folder)
