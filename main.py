#!/usr/bin/env python3
from datetime import datetime
from pathlib import PurePath
from typing import Optional, Union


# Waypoint 1:
def read_log_file(log_file_pathname: Union[str, bytes, PurePath]) -> bytes:
    """Read Game Session Log File.

    Args:
        log_file_pathname: The pathname of a Far Cry server log file.

    Returns: All the bytes from the file.

    """
    try:
        with open(log_file_pathname, 'rb') as f:
            return f.read()
    except OSError:
        return b''


def parse_log_variables(log_data: bytes):
    try:
        log_data_lines = log_data.decode().splitlines()
    except Exception:
        pass


# Waypoint 2, 3:
def parse_log_start_time(log_data: bytes) -> Optional[datetime]:
    """Parse Far Cry Engine's Start Time.

    Args:
        log_data: The data read from a Far Cry server's log file.

    Returns: The time the Far Cry engine began to log events.

    """
    try:
        log_data_lines = log_data.decode().splitlines()
        latter = log_data_lines[0]
        start_time = datetime.strptime(latter[15:], '%A, %B %d, %Y %H:%M:%S')

        return start_time
    except (ValueError, LookupError):
        return None


if __name__ == '__main__':
    log = read_log_file('./logs/log00.txt')
    parse_log_start_time(log)
