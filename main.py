#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from logging import error
from pathlib import PurePath
from re import search
from typing import Optional, Union

START_TIME_PATTERN = r'Log Started at (\w+, \w+ \d{2}, \d{4} ' \
                     r'\d{2}:\d{2}:\d{2})'
TIME_ZONE_PATTERN = r'cvar: \(g_timezone,(-?\d)'


# Waypoint 1:
def read_log_file(log_file_pathname: Union[str, bytes, PurePath]) -> str:
    """Read Game Session Log File.

    Args:
        log_file_pathname: The pathname of a Far Cry server log file.

    Returns: All the bytes from the file.

    """
    try:
        with open(log_file_pathname) as f:
            return f.read()
    except OSError as e:
        error(e, exc_info=True)
        return ''


# Waypoint 2, 3:
def parse_log_start_time(log_data: str) -> Optional[datetime]:
    """Parse Far Cry Engine's Start Time.

    Args:
        log_data: The data read from a Far Cry server's log file.

    Returns: The time the Far Cry engine began to log events.

    """
    try:
        start_time_log = search(START_TIME_PATTERN, log_data)
        start_time = datetime.strptime(start_time_log.group(1),
                                       '%A, %B %d, %Y %H:%M:%S')

        timezone_log = search(TIME_ZONE_PATTERN, log_data)
        tzinfo = timezone(timedelta(hours=int(timezone_log.group(1))))
        return start_time.replace(tzinfo=tzinfo)
    except (ValueError, LookupError, AttributeError) as e:
        error(e, exc_info=True)
        return None


if __name__ == '__main__':
    log = read_log_file('./logs/log.txt')
    start = parse_log_start_time(log)
    print(repr(start))
