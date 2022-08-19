"""Backup soft

Made by Leonid (https://t.me/G4m3_80ft)
"""
import os
import sys
import shutil
import time
import logging
import threading
import json

ACTION_TYPES: tuple = ("archive", "archive_and_del", "sync")
ACTION_SETTING_NAMES: tuple = ("name", "on_start", "time", "setup")


def main() -> None:
    logger.debug('Program started')
    read_config()
    return None


def read_config() -> None:
    if not os.path.exists('config.json'):
        logger.critical('Config not found')
        with open('config.json', 'w') as cnfg:
            cnfg.write('\'{\n\t"config": [\n\t\t{\n\t\t\t"archive": {\n\t\t\t'
                       '\t"name": "archive",\n\t\t\t\t"on_start": false,\n\t\t'
                       '\t\t"time": {\n\t\t\t\t\t\t"%d %m %Y %H:%M": "01 Jan 2000 00:0'
                       '0"\n\t\t\t\t},\n\t\t\t\t"setup": {\n\t\t\t\t\t"from_pa'
                       'th": "PATH",\n\t\t\t\t\t"to_path": "PATH"\n\t\t\t\t}\n'
                       '\t\t\t}\n\t\t},\n\t\t{\n\t\t\t"archive_and_del": {\n\t'
                       '\t\t\t"name": "archive_and_del",\n\t\t\t\t"on_start": '
                       'false,\n\t\t\t\t"time": {\n\t\t\t\t\t\t"%d %m %Y %H:%M": '
                       '"01 Jan 2000 00:00"\n\t\t\t\t},\n\t\t\t\t"setup": {\n\t\t\t'
                       '\t\t"from_path": "PATH",\n\t\t\t\t\t"to_path": "PATH"'
                       '\n\t\t\t\t}\n\t\t\t}\n\t\t},\n\t\t{\n\t\t\t"sync": {\n'
                       '\t\t\t\t"name": "sync",\n\t\t\t\t"on_start": false,\n'
                       '\t\t\t\t"time": {\n\t\t\t\t\t\t"%d %m %Y %H:%M": "01 Jan 2000'
                       '00:00"\n\t\t\t\t},\n\t\t\t\t"setup": {\n\t\t\t\t\t"pat'
                       'hs_to_sync": [\n\t\t\t\t\t\t"PATH1",\n\t\t\t\t\t\t"PAT'
                       'H2"\n\t\t\t\t\t]\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t]\n}'
                       '\''.replace('\t', '  '))
        logger.warning('Sample config created, setup required')
        return None

    with open('config.json', 'r') as config:
        config = json.load(config)
    logger.debug('Config loaded')

    if not isinstance(config, dict):
        logger.critical('Invalid config: dict (JS object) expected')
        raise TypeError('dict (JS object) expected')
    elif "config" not in config.keys():
        logger.critical('Invalid config: no "config" key')
        raise KeyError("config")
    logger.debug('Config is correct')

    config = config["config"]

    for action in config:
        handle_action(action)

    return None


def handle_action(action: dict) -> None:
    global ACTION_TYPES, ACTION_SETTING_NAMES

    if not isinstance(action, dict):
        logger.error('Invalid action: dict (JS object) expected')
        return
    elif len(action) != 1:
        logger.error('Invalid action: unexpected length')
        return
    elif action_type := tuple(action)[0] not in ACTION_TYPES:
        logger.error(f'Invalid action: unknown action ({action_type})')
        return
    for action_type in ACTION_TYPES:
        if action_type not in action:
            continue
        action_settings: dict = action[action_type]
        if not isinstance(action_settings, dict):
            logger.warning(f'Invalid action "{action_type}" settings: '
                           'dict (JS object) expected')
            continue
        elif len(action_settings) != 4:
            logger.warning(f'Invalid action "{action_type}" settings: '
                           'unexpected length')
            continue
        elif set(action_settings) != set(ACTION_SETTING_NAMES):
            logger.warning(f'Invalid action "{action_type}" settings: '
                           f'wrong keys: {tuple(action_settings)}')
            continue
        logger.debug(f'Action "{action_settings["name"]}" ({action_type})'
                     'settings are correct')
        action_func = globals()[action_type]
        if action_settings.pop("on_start"):
            action_func(**action_settings["setup"])
            time.sleep(1)
        threading.Thread(
            wait_for_activation(action_settings['name'],
                                action_func,
                                action_settings['time'],
                                action_settings['setup']
                                )
        ).start()

        return None


def wait_for_activation(action_name: str, action_func, action_time: dict,
                        action_settings: dict) -> None:
    time_format: str = tuple(action_time)[0]
    time_setting: str = action_time[time_format]

    minute: int = 60
    hour: int = 60 * minute
    day: int = 24 * hour
    week: int = 7 * day
    month: int = 31 * day
    year: int = 366 * day
    delay_between_checks: int = 1
    delay_after_doing: int = 1
    if '%M' in time_format:
        delay_between_checks = minute // 4
        delay_after_doing = minute
    elif any((i in time_format for i in ('%H', '%I'))):
        delay_between_checks = hour // 4
        delay_after_doing = hour
    elif any((i in time_format for i in ('%d', '%j'))):
        delay_between_checks = 3 * hour
        delay_after_doing = day
    elif any((i in time_format for i in ('%U', '%W'))):
        delay_between_checks = day
        delay_after_doing = week
    elif any((i in time_format for i in ('%m', '%B', '%b'))):
        delay_between_checks = week
        delay_after_doing = month
    elif any((i in time_format for i in ('%Y', '%y'))):
        delay_between_checks = month
        delay_after_doing = year

    logger.debug(f'Action "{action_name}" started waiting for activation '
                 f'(delay between checks: {delay_between_checks}, '
                 f'delay after doing: {delay_after_doing})')
    while True:
        if is_time_right(time_format, time_setting) and has_no_delay(action_name):
            action_func(**action_settings)
            set_delay(action_name, delay_after_doing)
        time.sleep(delay_between_checks)


def is_time_right(time_format: str, time_setting: str) -> bool:
    """Checks time

    >>> import time
    >>> is_time_right("%H", time.strftime("%H"))
    True
    >>> is_time_right("%S", time.strftime("%M"))
    False
    """
    return time.strftime(time_format) == time_setting


def has_no_delay(name_to_check: str) -> bool:
    """Checks delay in done.json

    >>> import json
    >>> has_no_delay("existing_name")
    False
    >>> has_no_delay("non_existing_name")
    True
    """

    done: dict = load_done()

    for name, time_to_wait in done.items():
        if name == name_to_check:
            return time_to_wait <= time.time()
    else:
        return True


def set_delay(name: str, delay: int) -> None:
    done: dict = load_done()
    done[name] = delay
    with open('done.json', 'r') as done_fp:
        json.dump(done, done_fp, indent=2)
    logger.debug(f'Set delay ({delay} secs) for "{name}"')

    return None


def load_done() -> dict:
    """Loads done.json

    >>> import json
    >>> load_done()
    {'existing_name': 100000000000000000000}
    """

    with open('done.json', 'r') as done:
        done = json.load(done)

    if not isinstance(done, dict):
        logger.critical('Invalid JSON: dict (JS object) expected')
        raise TypeError('dict (JS object) expected')
    elif "done" not in done.keys():
        logger.critical('Invalid JSON: no "done" key')
        raise KeyError("done")

    logger.debug('"done.json" loaded correctly')
    return done["done"]


def setup_logger(lgr: logging.Logger) -> None:
    lgr.setLevel(10)
    formatter: logging.Formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] '
        '\"%(message)s\" in file %(pathname)s'
    )

    level: int = 0
    if len(sys.argv) < 2:
        level = 20
    elif sys.argv[1].isdigit():
        level = int(sys.argv[1])

    handlers: tuple = get_handlers()
    set_formatter(formatter, handlers)

    for handler in handlers:
        handler.setLevel(level)
        lgr.addHandler(handler)

    lgr.debug(f'Logger set (level: {level})')

    return None


def get_handlers() -> tuple:
    stdout_handler: logging.Handler = logging.StreamHandler(sys.stdout)
    logfile_handler: logging.Handler = logging.FileHandler('Dan7.log')

    return stdout_handler, logfile_handler


def set_formatter(formatter: logging.Formatter, handlers: tuple) -> None:
    for handler in handlers:
        handler.setFormatter(formatter)

    return None


def sync(paths_to_sync: list) -> None:
    check_paths(*paths_to_sync)

    paths: dict = get_paths(paths_to_sync)
    paths: dict = filter_paths(paths)
    create_dirs_and_files(paths)
    logger.info(f'Paths {paths_to_sync} synced')

    return None


def get_paths(tops: list) -> dict:
    paths: dict = {}

    for top in tops:
        top: str = os.path.abspath(top)
        paths[top]: list = [].copy()

        for dirpath, dirnames, filenames in os.walk(top):
            dirpath = dirpath[len(top):]

            for path in dirnames + filenames:
                paths[top].append(dirpath + os.sep + path)
                if len(paths[top]) > 50:
                    break

        paths[top] = sorted(paths[top], key=len)

    logger.debug(f'Paths {tops} scanned')

    return paths


def filter_paths(paths: dict) -> dict:
    for top, rel_paths in paths.items():
        for other_top in paths:
            if other_top == top:
                continue
            for rel_path in rel_paths:
                if rel_path not in paths[other_top]:
                    continue

                if (round(os.path.getmtime(top + rel_path))
                        == round(os.path.getmtime(other_top + rel_path))):
                    continue
                elif (round(os.path.getmtime(top + rel_path))
                      > round(os.path.getmtime(other_top + rel_path))):
                    paths[top].remove(rel_path)
                else:
                    paths[other_top].remove(rel_path)

    logger.debug(f'Paths {tuple(paths)} filtered')

    return paths


def create_dirs_and_files(paths: dict) -> None:
    for top, rel_paths in paths.items():
        for other_top in paths:
            if other_top == top:
                continue
            for rel_path in rel_paths:
                if os.path.isdir(top + rel_path):
                    os.mkdir(other_top + rel_path)
                elif os.path.isfile(top + rel_path):
                    shutil.copy2(top + rel_path, other_top + rel_path)

    logger.debug(f'Paths {tuple(paths)} created')

    return None


def archive(from_path: str, to_path: str = os.getcwd()) -> None:
    from_path = os.path.normpath(from_path)
    to_path = os.path.normpath(to_path)

    check_paths(from_path, to_path)
    shutil.make_archive(to_path + os.sep + time.strftime('%d.%m.%y_%H-%M-%S'),
                        'zip', from_path)

    logger.info(f'Archived from "{from_path}" to "{to_path}"')

    return None


def archive_and_del(from_path: str, to_path: str = os.getcwd()) -> None:
    archive(from_path, to_path)
    shutil.rmtree(from_path, True)

    logger.info(f'Removed tree "{from_path}"')

    return None


def check_paths(*paths) -> None:
    for path_ in paths:
        if not os.path.exists(path_):
            logger.critical(f'No such directory: {repr(path_)}')
            raise FileNotFoundError(f'No such directory: {repr(path_)}')

    return None


if __name__ == '__main__':
    logger: logging.Logger = logging.getLogger(__name__)
    setup_logger(logger)

    if '0' in sys.argv:
        sys.argv.append('-v')
        import doctest
        doctest.testmod()
        del doctest

    try:
        main()
    except:
        logger.critical('CRITICAL ERROR!',
                        exc_info=sys.exc_info())
    logger.info('Program stopped')
