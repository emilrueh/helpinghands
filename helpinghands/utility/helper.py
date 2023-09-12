from ..utility.logger import get_logger

import sys, subprocess, platform, traceback, inspect
from termcolor import colored
from typing import Type


# EXCEPTIONS
def log_exception(
    e: BaseException, log_level: str = "warning", verbose=False, tb_limit=4
) -> str:
    logger = get_logger()
    """
    Logs an exception with a specified log level.

    Parameters:
        e: The exception to be logged.
        log_level: The log level for the exception. Defaults to "warning".

    Returns:
        str: The name of the exception type.
    """

    # Get the file name and line number where the exception occurred
    frame = inspect.currentframe()
    file_name = inspect.getframeinfo(frame.f_back).filename
    line_number = inspect.getframeinfo(frame.f_back).lineno

    message = (
        f"{type(e).__name__} in {file_name}:{line_number}: {str(e).split('  ')[0]}"
    )

    if verbose:
        tb_str = traceback.format_exception(type(e), e, e.__traceback__, limit=tb_limit)
        trace = "\n".join(tb_str)
        traceback_message = f"\n\n--- Stack Trace ---\n{trace}\n--------------------\n"
        message += traceback_message

    log_levels = {
        "debug": logger.debug,
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "exception": logger.exception,
        "critical": logger.critical,
    }

    log_function = log_levels.get(log_level, logger.warning)
    log_function(message)

    return type(e).__name__


# GITHUB
def get_git_tree(repo_path="."):
    def create_tree_string(tree, indent=""):
        tree_string = ""
        for name, node in tree.items():
            tree_string += f"{indent}{name}\n"
            if isinstance(node, dict):
                tree_string += create_tree_string(node, indent + "    ")
        return tree_string

    # Get list of files in repository
    result = subprocess.run(
        ["git", "ls-files"], capture_output=True, cwd=repo_path, text=True
    )
    files = result.stdout.split("\n")

    # Build and print directory tree
    tree = {}
    for file in files:
        path = file.split("/")
        node = tree
        for part in path:
            node = node.setdefault(part, {})
    return create_tree_string(tree)


# OTHER
def colorize(text, color="yellow", background=None, style=None):
    if (
        sys.stdout.isatty()
    ):  # Only colorize if output is going to a terminal (excluding jupyter nb)
        return colored(text, color, background, style)
    else:
        return text


def get_variable_name(variable):
    return [k for k, v in globals().items() if v is variable][0]


def ensure_windows_os():
    """Ensures that the current OS is Windows. Raises an error otherwise."""
    if platform.system() != "Windows":
        raise NotImplementedError("This function is only available on Windows!")
