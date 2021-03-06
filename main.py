#!/usr/bin/env python3
from csv import writer
from datetime import datetime, timedelta, timezone
from logging import basicConfig, DEBUG, error, warning
from os.path import expanduser
from re import compile as re_compile, findall, M, search
from sqlite3 import connect as sqlite_connect, \
    Connection as sqlite_Connection, DatabaseError as sqlite_DatabaseError
from typing import Any, Dict, List, Optional, Sequence, Tuple

from psycopg2 import connect as pg_connect, DatabaseError as pg_DatabaseError

# RegEx Patterns:
START_TIME_PATTERN = r'^Log Started at (\w+, \w+ \d{2}, \d{4} ' \
                     r'\d{2}:\d{2}:\d{2})$'
TIME_ZONE_PATTERN = r'cvar: \(g_timezone,(-?\d)'
LOADING_LEVEL_PATTERN = r'Loading level Levels\/(\w+), mission (\w+)'
FRAG_PATTERN = r'^<([0-5][0-9]):([0-5][0-9])> <\w+> ([\w+ ]*) killed ' \
               r'(?:itself|([\w+ ]*) with (\w+))'
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
        with open(expanduser(log_file_pathname)) as f:
            return f.read()
    except OSError as e:
        error(e, exc_info=True)
        return ''


# Waypoint 2, 3:
def parse_log_start_time(log_data: str) -> datetime:
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
            warning("Can't get start time from the log file!")
            raise
        timezone_log = search(TIME_ZONE_PATTERN, log_data)
        if timezone_log:
            tzinfo = timezone(timedelta(hours=int(timezone_log.group(1))))
            return start_time.replace(tzinfo=tzinfo)
        return start_time
    except (ValueError, LookupError) as e:
        error(e, exc_info=True)


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
    warning("Can't get match mode and map from the log file!")
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
def parse_match_start_and_end_times(log_data: str,
                                    log_start: datetime,
                                    frags: List[Tuple[datetime, Any]]) \
        -> Sequence[datetime]:
    """Determine Game Session's Start and End Times.

    Args:
        log_data: The data read from a Far Cry server's log file.
        log_start: The time the Far Cry engine began to log events.
        frags: A list of tuples of the frags.

    Returns: The approximate start and end time of the game session.

    """
    start_time = _parse_start_time(log_data, log_start)
    last_frag_time = frags[-1][0]
    end_time = _parse_end_time(log_data, last_frag_time)
    return start_time, end_time


def _parse_start_time(data: str, start: datetime) -> datetime:
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


def _parse_end_time(data: str, start: datetime) -> datetime:
    """Get the game session's end time."""
    minute, second = None, None
    statistic_match = search(STATISTICS_PATTERN, data, M)
    if statistic_match:
        minute, second = statistic_match.groups()
    else:
        last_frag = search(FRAG_PATTERN, data, M)
        if last_frag:
            time_after_frags = re_compile('<([0-5][0-9]):([0-5][0-9])>') \
                .match(data, last_frag.end() + 1)
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


# Waypoint 9:
def write_frag_csv_file(log_file_pathname: Any,
                        frags: List[Tuple[datetime, Any]]) -> None:
    """Create Frag History CSV File.

    Args:
        log_file_pathname: The pathname of the CSV file to store the frags in
        frags: An array of tuples of the frags.

    """
    try:
        with open(expanduser(log_file_pathname), 'w') as f:
            csv_writer = writer(f)
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
    insert_statement = '''INSERT INTO match (start_time, end_time, game_mode, 
    map_name) VALUES (?,?,?,?)'''
    try:
        with sqlite_connect(file_pathname) as conn:
            cur = conn.cursor()
            cur.execute(insert_statement,
                        (start_time, end_time, game_mode, map_name))
            insert_frags_to_sqlite(conn, cur.lastrowid, frags)
            return cur.lastrowid
    except sqlite_DatabaseError as e:
        error(e, exc_info=True)
        return 0


# Waypoint 26:
def insert_frags_to_sqlite(connection: sqlite_Connection, match_id: int,
                           frags: List[Tuple[datetime, Any]]) -> None:
    """Insert Match Frags into SQLite.

     This function inserts new records into the table match_frag.

    Args:
        connection: A sqlite3 Connection object.
        match_id: The identifier of a match.
        frags: A list of frags.

    """
    cur = connection.cursor()
    for frag in frags:
        if len(frag) > 2:
            cur.execute("""INSERT INTO match_frag (match_id, frag_time, 
            killer_name, victim_name, weapon_code) VALUES (?,?,?,?,?)""",
                        (match_id, *frag))
        else:
            cur.execute(
                """INSERT INTO match_frag (match_id, frag_time, killer_name) 
                VALUES (?,?,?)""", (match_id, *frag))


# Waypoint 48:
def insert_match_to_postgresql(properties: Sequence[Optional[str]],
                               start_time: datetime,
                               end_time: datetime,
                               game_mode: str,
                               map_name: str,
                               frags: List[Tuple[datetime, Any]]) -> str:
    """Insert Game Session Data to PostgreSQL Database.

    This function inserts a new record into the table `match` with the
    arguments start_time, end_time, game_mode, and map_name, using an
    INSERT statement.

    This function inserts all the frags into the table `match_frag`.

    Args:
        properties: A tuple of the following form:
                    (hostname, database_name, username, password)
                    where:
                        - hostname: hostname of the PosgtreSQL server to
                        connect to;
                        - database_name: name of the database to use;
                        - username: username of the database account on which
                        the connection is being made;
                        - password: password of the database account.
        start_time: A datetime.datetime object with time zone information
                    corresponding to the start of the game session;
        end_time:   A datetime.datetime object with time zone information
                    corresponding to the end of the game session;
        game_mode:  Multi-player mode of the game session;
        map_name:   Name of the map that was played;
        frags:      A list of tuples in the following form:
                    (frag_time, killer_name[, victim_name, weapon_code])
                    where:
                        - frag_time (required): datetime.datetime with time
                        zone when the frag occurred;
                        - killer_name (required): username of the player who
                        fragged another or killed himself;
                        - victim_name (optional): username of the player who
                        has been fragged;
                        - weapon_code (optional): code of the weapon that was
                        used to frag.

    Returns: The identification of the match that has been inserted.

    """
    connection_string = "host={} dbname={} user={} password={}" \
        .format(*(i if i else "''" for i in properties))
    try:
        with pg_connect(connection_string) as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as curs:
                # Inserts a new record into the table `match`:
                curs.execute("""INSERT INTO match (start_time, end_time, 
                game_mode, map_name) VALUES (%s, %s, %s, %s)
                RETURNING match_id""",
                             (start_time, end_time, game_mode, map_name))
                match_id = curs.fetchone()[0]
                if match_id:
                    insert_frags_to_postgresql(conn, match_id, frags)
                return match_id
    except (pg_DatabaseError, TypeError) as exc:
        error("{}: {}".format(exc.__class__.__name__, exc))
        raise


def insert_frags_to_postgresql(connection: pg_connect, match_id: str,
                               frags: List[Tuple[datetime, Any]]) -> None:
    """Insert Match Frags into SQLite.

     This function inserts new records into the table match_frag.

    Args:
        connection: A sqlite3 Connection object.
        match_id: The identifier of a match.
        frags: A list of frags.

    """
    curs = connection.cursor()
    for frag in frags:
        if len(frag) == 2:
            curs.execute(
                """INSERT INTO match_frag (match_id, frag_time, killer_name) 
                VALUES (%s, %s, %s)""", (match_id, *frag))
        if len(frag) == 4:
            curs.execute("""INSERT INTO match_frag (match_id, frag_time, 
            killer_name, victim_name, weapon_code)
            VALUES (%s, %s, %s, %s, %s)""", (match_id, *frag))


# Waypoint 53:
def calculate_serial_killers(frags: List[Tuple[datetime, Any]]) \
        -> Dict[str, List[Tuple[datetime, str, str]]]:
    """Determine Serial Killers.

    Args:
        frags: A list of frags.

    Returns: A dictionary of killers with their longest kill series, where the
             key corresponds to the name of a player and the value corresponds
             to a list of frag times which contain the player's longest series.

    """
    serial_killers = {}
    for frag in frags:
        if len(frag) == 2:
            serial_killers.setdefault(frag[1], []).append([])
        if len(frag) == 4:
            serial_killers.setdefault(frag[1], [[]])[-1].append(
                (frag[0], frag[2], frag[3]))
            serial_killers.setdefault(frag[2], []).append([])
    return _get_longest_series(serial_killers)


# Waypoint 54:
def calculate_serial_losers(frags: List[Tuple[datetime, Any]]) \
        -> Dict[str, List[Tuple[datetime, str, str]]]:
    """Determine Serial Losers.

    Args:
        frags: A list of frags.

    Returns: a dictionary of killers with their longest death series, where the
             key corresponds to the name of a player and the value corresponds
             to a list of frag times of the player's longest series.

    """
    serial_losers = {}
    for frag in frags:
        if len(frag) == 2:
            serial_losers.setdefault(frag[1], [[]])[-1] \
                .append((frag[0], None, None))
        if len(frag) == 4:
            serial_losers.setdefault(frag[2], [[]])[-1] \
                .append((frag[0], frag[1], frag[3]))
            serial_losers.setdefault(frag[1], []).append([])
    return _get_longest_series(serial_losers)


def _get_longest_series(dictionary: Dict) -> Dict:
    """Find the longest streak of players.

    Args:
        dictionary: A dictionary of players with their series.

    Returns: A dictionary of players with their longest series.

    """
    tmp_dict = dictionary.copy()
    for player, series in tmp_dict.items():
        tmp_dict[player] = max(series, key=len)
    return tmp_dict


def main() -> None:
    """Running and Testing."""
    # Do basic configuration for the logging system:
    basicConfig(level=DEBUG,
                format="%(levelname)s: %(funcName)s():%(lineno)i: %(message)s")
    # Running:
    # properties = ('localhost', 'farcry', None, None)
    # files = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
    #          '10', '11']
    # for f in files:
    #     log_data = read_log_file('./logs/log' + f + '.txt')
    #     log_start_time = parse_log_start_time(log_data)
    #     game_mode, map_name = parse_match_mode_and_map(log_data)
    #     frags = parse_frags(log_data)
    #     start_time, end_time = parse_match_start_and_end_times(
    #         log_data, log_start_time, frags)
    #     if start_time and end_time:
    #         insert_match_to_postgresql(properties, start_time, end_time,
    #                                    game_mode, map_name, frags)
    # print(str(start_time), str(end_time))
    # write_frag_csv_file('./logs/log04.csv', frags)
    # print(insert_match_to_sqlite('./farcry.db', start_time, end_time,
    #                              game_mode, map_name, frags))
    log_data = read_log_file('./logs/log08.txt')
    # log_start_time = parse_log_start_time(log_data)
    # game_mode, map_name = parse_match_mode_and_map(log_data)
    frags = parse_frags(log_data)
    # prettified_frags = prettify_frags(frags)
    # print('\n'.join(prettified_frags))
    # start_time, end_time = parse_match_start_and_end_times(log_data,
    #                                                        log_start_time,
    #                                                        frags)
    # print(insert_match_to_postgresql(properties, start_time, end_time,
    #                                  game_mode, map_name, frags))
    # serial_killers = calculate_serial_killers(frags)
    # for player_name, kill_series in serial_killers.items():
    #     print('[%s]' % player_name)
    #     print('\n'.join([', '.join(([str(e) for e in kill]))
    #                      for kill in kill_series]))
    serial_losers = calculate_serial_losers(frags)
    for player_name, death_series in serial_losers.items():
        print('[%s]' % player_name)
        print('\n'.join([', '.join(([str(e) for e in death]))
                         for death in death_series]))


if __name__ == '__main__':
    main()
