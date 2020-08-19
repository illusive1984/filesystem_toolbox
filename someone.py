#!/usr/bin/python3
# -*- coding=utf-8 -*-
"""Script description goes here

This script do stuff.
"""

__author__ = "someone"
__copyright__ = "Copyright 2020, someone"
__credits__ = ["Jon Doe"]
__license__ = ""
__version__ = "0.0.1"
__maintainer__ = ""
__email__ = ""
__status__ = "Production"
__description__ = """butter.py bietet Funktionalitäten, rund um das Dateisystem BTRFS."""
__notes__ = """
butter.py [options]\n
              -h		Hilfe\n
              -D		Debug
              -d		snapold/ snapnew/ vergleiche Inhalt von Snapshots
              -v		verbose
              -c		erstellt ein neues BTRFS Subvolume
              -p		erstellt einen Ordner im Pfad für Snapshots
              -r		erstellt rekursiv die Order im Pfad für Snapshpots
              
"""
__deps__ = ['python3-psutil', 'python3-btrfs', 'python3-pyfiglet']
__dependencies__ = """
>>> Hello there!
>>> You need to install some python dependencies to run this script.
>>> Deps:
...     - {}
""".format('\n...     - '.join(__deps__))

from time import sleep
import argparse
import logging
import sys
from os import system

from pprint import pprint


def get_max_str_len_from_list_of_dict(list_of_dict):
    max_len = 0
    for line in list_of_dict:
        log.debug(line.values())
        _value_lens = [len(str(val)) for val in line.values()]
        _cur_len = max(_value_lens)
        if _cur_len >= max_len:
            max_len = _cur_len
    return max_len


def print_slow(text):
    words = text
    print('>>> ', end='')
    for char in words:
        sleep(0.02)
        sys.stdout.write(char)
        sys.stdout.flush()
    print('')


def print_table(list_of_dict):
    try:
        table_list = []

        col_names = [key.upper() for key in list_of_dict[0].keys()]
        log.debug('names: {}'.format(col_names))
        col_count = len(col_names)
        log.debug('count: {}'.format(col_count))
        max_len = get_max_str_len_from_list_of_dict(list_of_dict)

        log.debug('max_len: {}'.format(max_len + 5))
        col_len = '{:<' + str(max_len + 5) + '}'
        header_string = ' ' + col_len * col_count
        log.debug('header_string: {}'.format(header_string.upper()))
        table_list.append(' ' + '―' * (len(header_string.format(*col_names)) - 3) + ' ')
        table_list.append(header_string.format(*col_names))

        for row in list_of_dict:
            table_list.append(' ' + '―' * (len(header_string.format(*col_names)) - 3) + ' ')
            _line = header_string.format(*row.values())
            table_list.append(_line)

        table_list.append(' ' + '―' * (len(header_string.format(*col_names)) - 3) + ' ')

        for row in table_list:
            print(row)

    except Exception as e:
        print_slow("Ooops... can't print a table. Wrong data structure:\n{}".format(list_of_dict))
        print(e)


def install_dependencies():
    shrug = '\n\n\t\t¯\_(ツ)_/¯\n\n '
    try:
        system('clear')
        print(__dependencies__)
        print_slow("Should I try to install it for you? You need 'sudo'! [y|n]")
        input_answer = input(">>> ")

        if 'y' == input_answer.strip():
            print_slow('Okay, I will try to install this packages..\n')
            print('#' * 80)
            result = system('sudo apt install {}'.format(' '.join(__deps__)))
            print('#' * 80)
            if result != 0:
                print_slow('Ooooops, it looks like something wents wrong...')
                sleep(2)
                print_slow('Sorry... ' + shrug)
                return False
            print_slow('So, it looks like all packaged installed successfully.\n... Starting script in 3 seconds...\n')
            sleep(3)
            system('clear')
            return True
        else:
            print_slow("No? You really don't trust me?? :( OK! Bye! " + shrug)

    except KeyboardInterrupt:
        print_slow("No? You really don't trust me?? :( OK! Bye! " + shrug)
    return False


try:
    import psutil
    import btrfs
    import pyfiglet
except ModuleNotFoundError:
    if install_dependencies():
        import psutil
        import btrfs
        import pyfiglet
    else:
        exit(1)


class Logger:
    """ Logging Class to print log information by debug_level to file or tty.

    :param level: defines the loglevel.
        - WARNING
        - INFO (Default)
        - DEBUG
    :param file: Defines the logfile to write the output.
        If no file is given output is tty.
        Default is None
    :param date_format: Defines the formation of date time object.
        Default is <%Y-%m-%d %H:%M:%S>

    """

    def __init__(self, level='INFO', file='', date_format='%Y-%m-%d %H:%M:%S'):
        self.logger = logging
        self.log_level = level
        self.log_file = file
        self.date_format = date_format
        if not self.test_logfile():
            print('Logfile is not writable: {}'.format(self.log_file))
            exit(1)
        self.init_logger()

    def is_verbose_count(self):
        return isinstance(self.log_level, int)

    def test_logfile(self):
        if len(self.log_file) == 0:
            return True
        try:
            f = open(self.log_file, 'a')
            if f.writable():
                return True
        except:
            return False
        return False

    def init_logger(self):
        _level = logging.ERROR
        if not self.is_verbose_count():
            if self.log_level.upper() == 'WARNING':
                _level = logging.WARNING
            elif self.log_level.upper() == 'DEBUG':
                _level = logging.DEBUG
            else:
                _level = logging.INFO
        else:
            if self.log_level == 1:
                _level = logging.WARNING
            elif self.log_level == 2:
                _level = logging.INFO
            elif self.log_level >= 3:
                _level = logging.DEBUG

        self.logger.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=_level,
            datefmt=self.date_format,
            filename=self.log_file)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)


class FileSystem:
    def __init__(self):
        self.partitions = []
        self.update_part_infos()
        self.current_mp = None

    def update_part_infos(self):
        _idx = 0
        for p in psutil.disk_partitions():
            if 'squashfs' in p.fstype:
                continue
            self.partitions.append({
                'part_idx': _idx,
                'mountpoint': p.mountpoint,
                'fs_type': p.fstype,
                'disk_usage': '{} %'.format(psutil.disk_usage(p.mountpoint).percent),
                'device_name': p.device
            })
            _idx += 1

    def get_part_info(self):
        return self.partitions


def get_args():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-v', '--verbose',
                        action='count',
                        dest='debug_level',
                        default=0,
                        help="Set output more verbose")
    parser.add_argument('--dry-run',
                        action='store_true',
                        default=False,
                        dest='dry_run',
                        help="Do nothing, show only what's happen... ;) ")
    parser.add_argument('-r', '--create-recursive',
                        action='store_true',
                        default=False,
                        dest='create_recursive',
                        help='erstellt rekursiv die Order im Pfad für Snapshpots',
                        required=False)
    # required = parser.add_argument_group('required arguments')
    # required.add_argument('-s', '--snap-dir',
    #                       type=str,
    #                       action="store",
    #                       dest='snap_dir',
    #                       help='Warning threshold of the duration for the database query.',
    #                       required=True)
    args = parser.parse_args()
    return args


def main():
    system('clear')
    from pyfiglet import Figlet
    f = Figlet(font='slant')
    print(f.renderText('BTRFS Tool'))
    print_slow('I found some partitions. Here have a look at them.')
    print_table(FS.get_part_info())


if __name__ == '__main__':
    args = get_args()
    log = Logger(level=args.debug_level)
    FS = FileSystem()
    main()
