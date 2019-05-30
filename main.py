#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from logging import error, warning
from pathlib import PurePath
from re import findall, search
from typing import List, Optional, Sequence, Tuple, Union

START_TIME_PATTERN = r'Log Started at (\w+, \w+ \d{2}, \d{4} ' \
                     r'\d{2}:\d{2}:\d{2})'
TIME_ZONE_PATTERN = r'cvar: \(g_timezone,(-?\d)'
LOADING_LEVEL_PATTERN = r'Loading level Levels\/(\w+), mission (\w+)'
FRAG_PATTERN = r'<([0-5][0-9]):([0-5][0-9])> <\w+> ([\w+ ]*) killed ' \
               r'(?:itself|([\w+ ]*) with (\w+))'


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
        timezone_log = search(TIME_ZONE_PATTERN, log_data)
        if start_time_log:
            start_time = datetime.strptime(start_time_log.group(1),
                                           '%A, %B %d, %Y %H:%M:%S')
        else:
            warning("Something occurred with the log file!")
            return None
        if timezone_log:
            tzinfo = timezone(timedelta(hours=int(timezone_log.group(1))))
            return start_time.replace(tzinfo=tzinfo)
        return start_time
    except (ValueError, LookupError) as e:
        error(e, exc_info=True)
        return None


# Waypoint 4:
def parse_match_mode_and_map(log_data: str) -> Sequence[str]:
    """Parse Match Session's Mode and Map.

    Args:
        log_data: The data read from a Far Cry server's log file.

    Returns: A tuple (mode, map) where:
             mode: indicates the multi-player mode that was played, either
                   ASSAULT, TDM, or FFA;
             map: the name of the map that was used, for instance mp_surf.

    """
    match = search(LOADING_LEVEL_PATTERN, log_data)
    if match:
        return match.groups()
    warning("Something occurred with the log file!")
    return '', ''


# Waypoint 5, 6:
def parse_frags(log_data: str) -> List[Tuple[datetime, str]]:
    """Parse Frag History.

    Args:
        log_data: The data read from a Far Cry server's log file.

    Returns: A list of frags.

    """
    frags = []
    frag_time = parse_log_start_time(log_data)
    if frag_time:
        matches = findall(FRAG_PATTERN, log_data)
        for i, frag in enumerate(matches):
            frag_min = int(frag[0])
            frag_sec = int(frag[1])
            if (i == 0 and frag_min < frag_time.minute) or \
                    (i > 0 and frag_min < int(matches[i - 1][0])):
                # When the logged time reaches 59:59, it is reset to 00:00.
                frag_time += timedelta(hours=1)
            # Get the exact time of the frag log:
            frag_time = frag_time.replace(minute=frag_min, second=frag_sec)
            if frag[3] == '':
                frags.append((frag_time, frag[2]))
            else:
                frags.append((frag_time,) + frag[2:])
    else:
        warning("Something occurred with the log file!")
    return frags


if __name__ == '__main__':
    log = read_log_file('./logs/log00.txt')
    start = parse_log_start_time(log)
    mode, map = parse_match_mode_and_map(log)
    print(repr((parse_frags(log))))
