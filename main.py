#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from logging import error, warning
from pathlib import PurePath
from re import findall, search
from typing import List, Optional, Sequence, Tuple, Union

# RegEx Patterns:
START_TIME_PATTERN = r'Log Started at (\w+, \w+ \d{2}, \d{4} ' \
                     r'\d{2}:\d{2}:\d{2})'
TIME_ZONE_PATTERN = r'cvar: \(g_timezone,(-?\d)'
LOADING_LEVEL_PATTERN = r'Loading level Levels\/(\w+), mission (\w+)'
FRAG_PATTERN = r'<([0-5][0-9]):([0-5][0-9])> <\w+> ([\w+ ]*) killed ' \
               r'(?:itself|([\w+ ]*) with (\w+))'

# Emojis:
BLUE_CAR = "🚙"
GUN = "🔫"
BOMB = "💣"
ROCKET = "🚀"
KNIFE = "🔪"
SPEEDBOAT = "🚤"
STUCK_OUT_TONGUE = "😛"
FROWNING = "😦"
SKULL_AND_CROSSBONES = "☠"

# Weapon Codes with Emojis:
WEAPONS_DICT = {
    "Vehicle": BLUE_CAR,
    "Falcon": GUN,
    "Shotgun": GUN,
    "P90": GUN,
    "MP5": GUN,
    "M4": GUN,
    "AG36": GUN,
    "OICW": GUN,
    "SniperRifle": GUN,
    "M249": GUN,
    "VehicleMountedAutoMG": GUN,
    "VehicleMountedMG": GUN,
    "HandGrenade": BOMB,
    "AG36Grenade": BOMB,
    "OICWGrenade": BOMB,
    "StickyExplosive": BOMB,
    "Rocket": ROCKET,
    "VehicleMountedRocketMG": ROCKET,
    "VehicleRocket": ROCKET,
    "Machete": KNIFE,
    "Boat": SPEEDBOAT
}


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


# Waypoint 7:
def prettify_frags(frags: List[Tuple[datetime, str]]) -> List[str]:
    """Prettify Frag History.

    Args:
        frags: An array of tuples of frags parsed from a Far Cry server's
               log file

    Returns: A list of strings, each with a specified format.

    """
    strings = []
    for frag in frags:
        try:
            if len(frag) == 2:
                strings.append('[{}] {} {} {}'
                               .format(frag[0].isoformat(), FROWNING,
                                       frag[1], SKULL_AND_CROSSBONES))
            elif len(frag) == 4:
                strings.append('[{}] {} {} {} {} {}'
                               .format(frag[0].isoformat(), STUCK_OUT_TONGUE,
                                       frag[1], WEAPONS_DICT.get(frag[3]),
                                       FROWNING, frag[2]))
        except ValueError as e:
            error(e, exc_info=True)
            continue
    return strings


if __name__ == '__main__':
    log = read_log_file('./logs/log01.txt')
    start = parse_log_start_time(log)
    mode, map = parse_match_mode_and_map(log)
    frags = parse_frags(log)
    prettified_frags = prettify_frags(frags)
    print('\n'.join(prettified_frags))
    # print(repr((parse_frags(log))))
