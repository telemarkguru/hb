from ._path import (
    pathset,
    paths,
    stat,
    clear as path_clear,
    isdir,
    exists,
    newest,
    oldest,
    cwd,
    relative,
    directories,
    files,
    filter,
    root,
    anchor,
    statistics,
)

from ._read import load, scan, loaded_files, clear as read_clear


def clear():
    path_clear()
    read_clear()


__all__ = [
    "pathset",
    "paths",
    "stat",
    "isdir",
    "exists",
    "newest",
    "oldest",
    "cwd",
    "relative",
    "directories",
    "files",
    "filter",
    "root",
    "anchor",
    "statistics",
    "load",
    "scan",
    "loaded_files",
    "clear",
]
