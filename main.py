#!/usr/bin/env python3
from csv import writer
from datetime import datetime, timedelta, timezone
from logging import basicConfig, DEBUG, error, warning
from re import compile as re_compile, findall, M, search
from sqlite3 import connect, Connection, DatabaseError
from typing import Any, List, Optional, Sequence, Tuple

# RegEx Patterns:
START_TIME_PATTERN = r'^Log Started at (\w+, \w+ \d{2}, \d{4} ' \
                     r'\d{2}:\d{2}:\d{2})$'
TIME_ZONE_PATTERN = r'cvar: \(g_timezone,(-?\d)'
LOADING_LEVEL_PATTERN = r'Loading level Levels\/(\w+), mission (\w+)'
FRAG_PATTERN = r'^<([0-5][0-9]):([0-5][0-9])> <\w+> ([\w+ ]*) killed ' \
               r'(?:itself|([\w+ ]*) with (\w+))$'
LEVEL_LOADED_PATTERN = r'^<([0-5][0-9]):([0-5][0-9])>  Level \w+ loaded in ' \
                       r'[-+]?[0-9]*\.?[0-9]+ seconds$'
STATISTICS_PATTERN = r'^<([0-5][0-9]):([0-5][0-9])> == Statistics'

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
    "MG": GUN,
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
def read_log_file(log_file_pathname: Any) -> str:
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
        start_time_log = search(START_TIME_PATTERN, log_data, M)
        if start_time_log:
            start_time = datetime.strptime(start_time_log.group(1),
                                           '%A, %B %d, %Y %H:%M:%S')
        else:
            warning("Something occurred with the log file!")
            return None
        timezone_log = search(TIME_ZONE_PATTERN, log_data)
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
    found = search(LOADING_LEVEL_PATTERN, log_data, M)
    if found:
        return found.groups()[::-1]
    warning("Something occurred with the log file!")
    return '', ''


# Waypoint 5, 6:
def parse_frags(log_data: str) -> List[Tuple[datetime, Any]]:
    """Parse Frag History.

    Args:
        log_data: The data read from a Far Cry server's log file.

    Returns: A list of frags.

    """
    frags = []
    frag_time = parse_log_start_time(log_data)
    if frag_time:
        matches = findall(FRAG_PATTERN, log_data, M)
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
def prettify_frags(frags: List[Tuple[datetime, Any]]) -> List[str]:
    """Prettify Frag History.

    Args:
        frags: An array of tuples of frags parsed from a Far Cry server's
               log file.

    Returns: A list of strings, each with a specified format.

    """
    strings = []
    for frag in frags:
        try:
            if len(frag) == 2:
                strings.append('[{}] {} {} {}'
                               .format(frag[0], FROWNING, frag[1],
                                       SKULL_AND_CROSSBONES))
            elif len(frag) == 4:
                strings.append('[{}] {} {} {} {} {}'
                               .format(frag[0], STUCK_OUT_TONGUE,
                                       frag[1], WEAPONS_DICT.get(frag[3]),
                                       FROWNING, frag[2]))
        except ValueError as e:
            error('{} raised {}'.format(frag[0], e))
            continue
    return strings


# Waypoint 8:
def parse_game_session_start_and_end_times(log_data: str,
                                           log_start: Optional[datetime],
                                           frags: List[Tuple[datetime, Any]]) \
        -> Sequence[Optional[datetime]]:
    """Determine Game Session's Start and End Times.

    Args:
        log_data: The data read from a Far Cry server's log file.
        log_start: The time the Far Cry engine began to log events.
        frags: A list of tuples of the frags.

    Returns: The approximate start and end time of the game session.

    """
    start_time, end_time = None, None
    if log_start:
        start_time = _parse_start_time(log_data, log_start)
    if frags:
        last_frag_time = frags[-1][0]
        end_time = _parse_end_time(log_data, last_frag_time)
    return start_time, end_time


def _parse_start_time(data: str, start: datetime) -> Optional[datetime]:
    """Get the game session's start time."""
    level_loaded_match = search(LEVEL_LOADED_PATTERN, data, M)
    if level_loaded_match:
        minute, second = level_loaded_match.groups()
        start_time = start.replace(minute=int(minute),
                                   second=int(second))
        # When the logged time reaches 59:59, it is reset to 00:00.
        if start_time.minute < start.minute:
            start_time += timedelta(hours=1)
        return start_time
    warning("Something occurred with the data!")
    return None


def _parse_end_time(data: str, start: datetime) -> Optional[datetime]:
    """Get the game session's end time."""
    minute, second = None, None
    statistic_match = search(STATISTICS_PATTERN, data, M)
    if statistic_match:
        minute, second = statistic_match.groups()
    else:
        last_frag = search(FRAG_PATTERN + r'$', data)
        if last_frag:
            time_after_frags = re_compile('^<([0-5][0-9]):([0-5][0-9])>') \
                .match(data, last_frag.end())
            if time_after_frags:
                minute, second = time_after_frags.groups()
    if minute and second:
        end_time = start.replace(minute=int(minute),
                                 second=int(second))
        # When the logged time reaches 59:59, it is reset to 00:00.
        if end_time.minute < start.minute:
            end_time += timedelta(hours=1)
        return end_time
    warning("Something occurred with the data!")
    return None


# Waypoint 9:
def write_frag_csv_file(log_file_pathname: Any,
                        frags: List[Tuple[datetime, Any]]) -> None:
    """Create Frag History CSV File.

    Args:
        log_file_pathname: The pathname of the CSV file to store the frags in
        frags: An array of tuples of the frags.

    """
    try:
        with open(log_file_pathname, 'w') as f:
            csv_writer = writer(f, lineterminator='\n')
            csv_writer.writerows(frags)
    except OSError as e:
        error(e, exc_info=True)


# Waypoint 25:
def insert_match_to_sqlite(file_pathname: Any, start_time: datetime,
                           end_time: datetime,
                           game_mode: str,
                           map_name: str,
                           frags: List[Tuple[datetime, Any]]) -> int:
    """Insert Game Session Data into SQLite.

    Args:
        file_pathname: The path and name of the Far Cry's SQLite database.
        start_time: The start of the game session.
        end_time: The end of the game session.
        game_mode: Multi-player mode of the game session.
        map_name: Name of the map that was played.
        frags: A list of tuples of the frags.

    Returns: The identifier of the match that has been inserted.

    """
    insert_statement = "INSERT INTO match (start_time, end_time, game_mode, " \
                       "map_name) VALUES (?,?,?,?)"
    try:
        with connect(file_pathname) as conn:
            cur = conn.cursor()
            cur.execute(insert_statement,
                        (start_time, end_time, game_mode, map_name))
            insert_frags_to_sqlite(conn, cur.lastrowid, frags)
            return cur.lastrowid
    except DatabaseError as e:
        error(e, exc_info=True)
    return 0


# Waypoint 26:
def insert_frags_to_sqlite(connection: Connection, match_id: int,
                           frags: List[Tuple[datetime, Any]]) -> None:
    """Insert Match Frags into SQLite.

     This function inserts new records into the table match_frag.

    Args:
        connection: A sqlite3 Connection object.
        match_id: The identifier of a match.
        frags: a list of frags.

    """
    cur = connection.cursor()
    for frag in frags:
        if len(frag) > 2:
            cur.execute(
                "INSERT INTO match_frag (match_id, frag_time, killer_name, "
                "victim_name, weapon_code) VALUES (?,?,?,?,?)",
                (match_id, *frag))
        else:
            cur.execute(
                "INSERT INTO match_frag (match_id, frag_time, killer_name) "
                "VALUES (?,?,?)", (match_id, *frag))


def main() -> None:
    """Running and Testing."""
    # Do basic configuration for the logging system:
    basicConfig(level=DEBUG,
                format="%(levelname)s: %(funcName)s():%(lineno)i: %(message)s")
    # Running:
    log_data = read_log_file('./logs/log04.txt')
    log_start_time = parse_log_start_time(log_data)
    game_mode, map_name = parse_match_mode_and_map(log_data)
    frags = parse_frags(log_data)
    # prettified_frags = prettify_frags(frags)
    # print('\n'.join(prettified_frags))
    start_time, end_time = parse_game_session_start_and_end_times(
        log_data, log_start_time, frags)
    if start_time and end_time:
        # print(str(start_time), str(end_time))
        # write_frag_csv_file('./logs/log04.csv', frags)
        print(insert_match_to_sqlite('./farcry.db', start_time, end_time,
                                     game_mode, map_name, frags))


if __name__ == '__main__':
    main()
