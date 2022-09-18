"""
Cononical file paths with caching
"""

import os
import re
from os.path import abspath, normpath, dirname, relpath
from os import getcwd
from stat import S_ISDIR
from typing import Dict, Iterable, List


root = None  # root direcotory (found by scanning for .hbroot files)
current = None  # current directory


_comment = re.compile(r"#.*$")


def _find_root(path: str) -> str:
    parts = path.split("/")
    while parts:
        root = "/".join(parts)
        if os.path.exists(f"{root}/.hbroot"):
            return normpath(root)
        parts = parts[:-1]
    raise FileNotFoundError(f"Cannot find root given {path}")


def cwd() -> str:
    """Return canonical representation of current work directory"""
    return normpath(abspath(getcwd()))


def canonical(path: str, anchor: str = None) -> str:
    """Return canonical absolute path given a relative or absolute path
    The optiona anchor paramter gives the source directroy for relative
    paths. If not given, the current directory is used.

    Surplus "/xxx/../", "/./", "//" etc are removed.
    Symlinks are NOT expanded, as this is usually not what is wanted.
    """
    global root
    if not root:
        anchor = anchor or current or "."
        root = _find_root(anchor)
    if path.startswith("/"):
        path = f"{root}{path}"
    else:
        anchor = anchor or current
        path = f"{anchor}/{path}"
    path = normpath(path)
    if path.endswith("/,"):
        # Handle special case not covered by normpath
        path = path[:-2]
    return path


def pathset(*paths, anchor: str = None) -> Dict[str, bool]:
    """Create path set,
    Return a dict where the keys are canoical absolute paths.

    The optional anchor paramter gives the source directroy for relative
    paths. If not given, the current variable is used.

    The insert order is preserved.
    For duplicates,  the first inserted is kept.
    """
    pset = dict()
    anchor = anchor or current
    for path in paths:
        if isinstance(path, str):
            path = canonical(path, anchor)
            if path.endswith(".list"):
                pset.update(_explist(path))
            else:
                pset[path] = True
        elif isinstance(path, dict):
            pset.update(path)
        else:
            for p in path:
                pset.update(pathset(p, anchor=anchor))
    return pset


def paths(pathset: dict) -> Iterable[str]:
    """Return iterator for paths in pathset, in insertion order"""
    return pathset.keys()


def _explist(listfilepath: str) -> Dict[str, bool]:
    """Expand listfile (.list)
    Return pathset.
    """
    pset = dict()
    directory = listfilepath.rsplit("/", 1)[0]
    with open(listfilepath) as fh:
        for line in fh:
            line = _comment.sub("", line).strip()
            if not line:
                continue
            path = canonical(line, directory)
            if path.endswith(".list"):
                pset.update(_explist(path))
            else:
                pset[path] = True
    return pset


_stat_cache: Dict[str, os.stat_result] = {}
_stat_cnt = {"hit": 0, "miss": 0}


def stat(path: str) -> os.stat_result:
    """Return, possibly cached, file stats for a path

    Use cache to only access the file system once per path.
    clear() will clear the cache.
    """
    fstat = _stat_cache.get(path)
    if fstat:
        _stat_cnt["hit"] += 1
        return fstat
    fstat = os.stat(path)
    _stat_cache[path] = fstat
    _stat_cnt["miss"] += 1
    return fstat


def isdir(path: str) -> bool:
    """Reutrn True if path is a directory, False otherwise, usees
    path stat cache"""
    return S_ISDIR(stat(path).st_mode)


def newest(pathset: dict) -> str:
    """Return newest path in pathset"""
    return max(pathset, key=lambda x: stat(x).st_mtime)


def oldest(pathset: dict) -> str:
    """Return oldest path in pathset"""
    return min(pathset, key=lambda x: stat(x).st_mtime)


_dir_cache: Dict[str, str] = {}


def directories(pathset: Dict[str, bool]) -> Dict[str, bool]:
    """Return directory part of all paths in pathset"""
    pset = {}
    for path in pathset:
        p = _dir_cache.get(path)
        if not p:
            if isdir(path):
                p = path
            else:
                p = dirname(path)
            _dir_cache[path] = p
        pset[p] = True
    return pset


def relative(frompath: str, pathset: Dict[str, bool]) -> List[str]:
    """Return list of relative paths for all paths in pathset"""
    return [relpath(p, frompath) for p in pathset]


def clear():
    """Clear path caches"""
    _stat_cache.clear()
    _stat_cnt.update({"hit": 0, "miss": 0})
    _dir_cache.clear()
