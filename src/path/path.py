"""
Cononical file paths with caching
"""

import os
import re
from os.path import abspath, normpath
from os import getcwd


root = None
_comment = re.compile(r"#.*$")


def _find_root(path: str):
    parts = path.split("/")
    while parts:
        root = "/".join(parts)
        if os.path.exists(f"{root}/.hbroot"):
            return normpath(root)
        parts = parts[:-1]
    raise FileNotFoundError(f"Cannot find root given {path}")


def _fix_dots(path: str):
    parts = "/".split(path)

    try:
        while True:
            i = parts.index("..")
            del parts[i - 1 : i + 1]
    except ValueError:
        parts = [x for x in parts if x not in (".", "..")]
        return "/".join(parts)


def _cwd():
    """Return canonical representation of current work directory"""
    return normpath(abspath(getcwd()))


def canonical(path: str, anchor: str = None):
    """Return canonical absolute path given a relative or absolute path
    The optiona anchor paramter gives the source directroy for relative
    paths. If not given, the current directory is used.

    Surplus "/xxx/../", "/./", "//" etc are removed.
    Symlinks are NOT expanded, as this is usually not what is wanted.
    """
    global root
    if not root:
        anchor = anchor or _cwd()
        root = _find_root(anchor)
    if path.startswith("/"):
        path = f"{root}{path}"
    else:
        anchor = anchor or _cwd()
        path = f"{anchor}/{path}"
    path = normpath(path)
    if path.endswith("/,"):
        # Handle special case not covered by normpath
        path = path[:-2]
    return path


def pathset(*paths, anchor: str = None):
    """Create path set,
    Return a dict where the keys are conoical absolute paths.

    The optiona anchor paramter gives the source directroy for relative
    paths. If not given, the current directory is used.

    The insert order is preserved.
    For duplicates,  the first inserted is kept.
    """
    pset = dict()
    anchor = anchor or _cwd()
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
            pset.update(pathset(path))
    return pset


def paths(pathset):
    """Return iterator for paths in pathset, in insertion order"""
    return pathset.keys()


def _explist(listfilepath: str):
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


_stat_cache = {}
_stat_cnt = {"hit": 0, "miss": 0}


def stat(path):
    """Return, possibly cached, file stats for a path

    Use cache to only access the file system once per path.
    clear() will clear the cache.
    """
    stat = _stat_cache.get(path)
    if stat:
        _stat_cnt["hit"] += 1
        return stat
    stat = os.stat(path)
    _stat_cache[path] = stat
    _stat_cnt["miss"] += 1
    return stat


def clear():
    """Clear path stat cache"""
    _stat_cache.clear()
    _stat_cnt.update({"hit": 0, "miss": 0})


def isdir(path):
    """Reutrn True if path is a directory, False otherwise, usees
    path stat cache"""
    stat = stat(path)
    return stat.S_ISDIR(stat.st_mode)


def newest(pathset):
    """Return newest path in pathset"""
    return max(pathset, key=lambda x: stat(x).st_mtime)
