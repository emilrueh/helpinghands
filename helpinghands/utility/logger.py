import logging, os

from termcolor import colored
from datetime import datetime


LOGGER_NAME = "global_logger"


def get_logger() -> object:
    return logging.getLogger(LOGGER_NAME)


def config_logger(
    name: str = "base_logger:",
    lvl_console: str = "DEBUG",
    lvl_file: str = None,
    lvl_root: str = "INFO",
    fmt_console="%(name)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s",
    fmt_file="%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s",
    fmt_date: str = "%Y-%m-%d %H:%M:%S:Ms",
    file_name: str = "runtime",
    file_timestamp: str = "%Y%m%d-%H%M%S",
    logs_dir: str = "logs",
    prints: bool = False,
    encoding: str = None,
) -> object:
    global LOGGER_NAME
    LOGGER_NAME = name

    logger = logging.getLogger(name)

    if prints:  # can get improved
        if lvl_console and lvl_file:
            print(colored("Logging to console and file...", "cyan"))
        elif lvl_console:
            print(colored("Logging to console...", "cyan"))
        elif lvl_file:
            print(colored("Logging to file...", "cyan"))

    base_values_dict = {
        "name": name if name == "base_logger" else None,
        "lvl_console": lvl_console if lvl_console == "DEBUG" else None,
        "lvl_file": lvl_file if lvl_file is None else None,
        "lvl_root": lvl_root if lvl_root == "INFO" else None,
        "fmt_console": fmt_console
        if fmt_console == "%(name)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s"
        else None,
        "fmt_file": fmt_file
        if fmt_file
        == "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s"
        else None,
        "fmt_date": fmt_date if fmt_date == "%Y-%m-%d %H:%M:%S:Ms" else None,
        "file_name": file_name if file_name == "runtime" else None,
        "file_timestamp": file_timestamp if file_timestamp == "%Y%m%d-%H%M%S" else None,
        "logs_dir": logs_dir if logs_dir == "logs" else None,
        "prints": prints if prints == False else None,
        "encoding": encoding if encoding == None else None,
    }

    base_values = {key for key, value in base_values_dict.items() if value is not None}

    if base_values and prints:
        print(f"Starting with the base settings for {', '.join(base_values)}.")

    if file_timestamp:
        file_timestamp = datetime.now().strftime(file_timestamp)

    level_options = ["debug", "info", "warning", "exception", "error", "critical"]

    if lvl_file:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        f_handler = logging.FileHandler(
            filename=os.path.join(logs_dir, f"{file_name}_{file_timestamp}.log"),
            mode="a",
            encoding=encoding,
        )
        f_format = logging.Formatter(
            fmt=fmt_file,
            datefmt=fmt_date,
        )
        if lvl_file in level_options:
            lvl_file = logging.getLevelName(lvl_file.upper())
        else:
            default_lvl_file = "DEBUG"
            lvl_file = logging.getLevelName(default_lvl_file.upper())
            if prints:
                print(f"Set the file level to {default_lvl_file}.")

        f_handler.setLevel(lvl_file)
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)

    if lvl_console:
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter(
            fmt=fmt_console,
            datefmt=fmt_date,
        )
        if lvl_console in level_options:
            lvl_console = logging.getLevelName(lvl_console.upper())
        else:
            default_lvl_console = "DEBUG"
            lvl_console = logging.getLevelName(default_lvl_console.upper())
            if prints:
                print(f"Set the console level to {default_lvl_console}.")

        c_handler.setLevel(lvl_console)
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

    if lvl_root in level_options:
        logger.setLevel(lvl_root.upper())
    else:
        default_lvl_root = "DEBUG"
        logger.setLevel(default_lvl_root.upper())
        if prints:
            print(f"Set the root level to {default_lvl_root}.")
    return logger
