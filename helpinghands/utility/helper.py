import logging
from ..utility.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

import sys, subprocess, platform

from termcolor import colored


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
