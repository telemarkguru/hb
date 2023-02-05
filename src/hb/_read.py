"""
Read hb.py files
"""

from ._path import PathSet

import importlib
import importlib.util
import sys
from os import listdir
from os.path import dirname, exists
from typing import Tuple
from types import ModuleType


def _load_source(modname: str, filepath: str):
    spec = importlib.util.spec_from_file_location(modname, filepath)
    assert spec
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def load(hb_path: str) -> ModuleType:
    """Load hb.py Python file"""
    directory = dirname(hb_path)
    sys.path.insert(0, directory)
    mod = _load_source("read_hb", hb_path)
    sys.path.pop(0)
    return mod


def scan(
    directories: PathSet, filename="hb.py", scanned: PathSet = {}
) -> Tuple[PathSet, PathSet]:
    """Scan for files with a given name (default hb.py), in a
    set of directories and their parent directories (up until
    a .hbroot file is found or /).
    Return a pathset containing the found files, and a pathset
    containing the directories that were scanned.  The latter
    can be fed to subsequent calls to scan to avoid scanning
    directories more than once.
    """
    files = {}
    scanned = dict(scanned)
    for directory in directories:
        if directory in scanned:
            continue
        scanned[directory] = True
        if exists(directory):
            filenames = listdir(directory)
            if filename in filenames:
                files[f"{directory}/{filename}"] = True
                continue
            if ".hbroot" in files or directory == "/":
                continue
        f, s = scan({dirname(directory): True}, filename, scanned)
        files.update(f)
        scanned.update(s)
    return files, scanned
