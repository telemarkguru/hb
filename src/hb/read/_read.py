"""
Read hb.py files
"""

from .. import path

import importlib
import importlib.util
import sys
import os
from os.path import dirname, exists
from typing import Set, List


def _load_source(modname: str, filepath: str):
    spec = importlib.util.spec_from_file_location(modname, filepath)
    assert spec
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


_loaded_files: List[str] = []


def load(hb_path: str) -> None:
    """Load and run hb.py Python file"""
    directory = dirname(hb_path)
    last_anchor = path.anchor(directory)
    sys.path.insert(0, directory)
    mod = _load_source("read_hb", hb_path)
    sys.path.pop(0)
    path.anchor(last_anchor)
    _loaded_files.append(hb_path)
    return mod


_scanned: Set[str] = set()
_scan_queue: List[str] = []


def scan(directories_pathset: dict) -> None:
    """Scan for and load hb.py files in set of directories.

    When a hb.py file is found and loaded, there may be a need to scan
    more directories, so it is allowd to call scan() recursively.
    """
    global _scan_queue
    is_scanning = bool(_scanned)
    _scan_queue += list(directories_pathset.keys())
    if is_scanning:
        return
    while _scan_queue:
        directory = _scan_queue.pop()
        if directory not in _scanned:
            _scanned.add(directory)
            if exists(directory):
                files = os.listdir(directory)
                if "hb.py" in files:
                    load(f"{directory}/hb.py")
                elif ".hbroot" not in files and directory != "/":
                    scan({dirname(directory): True})
            else:
                scan({dirname(directory): True})
    _scanned.clear()
    _scan_queue.clear()


def loaded_files() -> List[str]:
    return _loaded_files


def clear() -> None:
    _loaded_files.clear()
