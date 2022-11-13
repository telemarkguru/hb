"""
Cononical file paths with caching
"""

import os
import re
from os.path import abspath, normpath, dirname, relpath
from os import getcwd
from stat import S_ISDIR
from typing import Dict, Iterable, List, Tuple, Union


_root = None  # root direcotory (found by scanning for .hbroot files)
_anchor = None
_comment = re.compile(r"#.*$")
_cwd = normpath(abspath(os.getcwd()))

# pathset type:
PathSet = Dict[str, bool]
AnyPath = Union[str, PathSet, Iterable[str], Iterable[Union[PathSet, str]]]


def _find_root(path: str) -> str:
    parts = path.split("/")
    while parts:
        root = "/".join(parts)
        if os.path.exists(f"{root}/.hbroot"):
            return normpath(root)
        parts = parts[:-1]
    raise FileNotFoundError(f"Cannot find root given {path}")


def anchor(path: str) -> str:
    """Set default anchor path, and return previous anchor"""
    global _anchor
    last_anchor = _anchor
    _anchor = path
    return last_anchor or ""


def root() -> str:
    """Return canonical representation of the root directory"""
    return _root or ""


def cwd() -> str:
    """Return canonical representation of current work directory"""
    return _cwd


def canonical(path: str, anchor: str = None) -> str:
    """Return canonical absolute path given a relative or absolute path
    The optiona anchor paramter gives the source directory for relative
    paths. If not given, the default anchor is used (set with anchor(path))

    Surplus "/xxx/../", "/./", "//" etc are removed.
    Symlinks are not expanded.
    """
    global _root
    if not _root:
        anchor = anchor or _anchor or "."
        _root = _find_root(anchor)
    if path[0] == "/":
        pass
    elif path.startswith("$root/"):
        path = path.replace("$root", _root, 1)
    else:
        anchor = anchor or _anchor
        path = f"{anchor}/{path}"
    path = normpath(path)
    # Handle special cases not covered by normpath:
    if path.endswith("/,"):
        path = path[:-2]
    if path.startswith("//"):
        path = path[1:]
    return path


def pathset(*paths: AnyPath, anchor: str = None) -> PathSet:
    """Create path set,
    Return a dict where the keys are canoical absolute paths.

    The optional anchor paramter gives the source directory for relative
    paths. If not given, the default anchor is used.

    The insert order is preserved.
    For duplicates,  the first inserted is kept.
    """
    pset = dict()
    anchor = anchor or _anchor
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


_explist_cache: Dict[str, PathSet] = {}


def _explist(listfilepath: str) -> PathSet:
    """Expand listfile (.list)
    Return pathset.
    """
    pset = _explist_cache.get(listfilepath, {})
    if pset:
        return pset
    directory = dirname(listfilepath)
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
    _explist_cache[listfilepath] = pset
    return pset


_stat_cache: Dict[str, os.stat_result] = {}
_stat_cnt = {"hit": 0, "miss": 0}
_default_stat = os.stat_result(
    (
        0x81B4,  # mode -rw-rw-r-- plain file
        0,  # inode
        0,  # device
        1,  # nlink
        0,  # uid
        0,  # gid
        0,  # size
        0,  # atime
        0,  # mtime
        0,  # ctime
    )
)


def stat(path: str) -> os.stat_result:
    """Return, possibly cached, file stats for a path,
    or False if the path does not exist.

    Use cache to only access the file system once per path.
    clear() will clear the cache.
    """
    fstat = _stat_cache.get(path)
    if fstat is not None:
        _stat_cnt["hit"] += 1
        return fstat
    try:
        fstat = os.stat(path)
    except FileNotFoundError:
        fstat = _default_stat
    _stat_cache[path] = fstat
    _stat_cnt["miss"] += 1
    return fstat


def isdir(path: str) -> bool:
    """Return True if path is a directory, False otherwise, usees
    path stat cache"""
    return S_ISDIR(stat(path).st_mode)


def exists(path: str) -> bool:
    """Return True if path exists, False otherwise, usees
    path stat cache"""
    return stat(path).st_ctime != 0


def newest(pathset: PathSet) -> str:
    """Return newest path in pathset"""
    return max(pathset, key=lambda x: stat(x).st_mtime)


def oldest(pathset: PathSet) -> str:
    """Return oldest path in pathset"""
    return min(pathset, key=lambda x: stat(x).st_mtime)


_dir_cache: Dict[str, str] = {}


def directories(pathset: PathSet) -> PathSet:
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


def files(pathset: PathSet) -> PathSet:
    """Return all files in pathset. I.e. skip directories"""
    return {path: True for path in pathset if not isdir(path)}


_FilterReturnType = Union[Tuple[PathSet, ...], PathSet]


def filter(pathset: PathSet, *patterns: str) -> _FilterReturnType:
    """Filter out paths matching a set of patterns
    Return one pathset per pattern"""
    regexps = [re.compile(x) for x in patterns]
    pathsets = tuple(
        {x: True for x in pathset if r.search(x)} for r in regexps
    )
    if len(pathsets) == 1:
        return pathsets[0]
    return pathsets


def relative(frompath: str, pathset: PathSet) -> List[str]:
    """Return list of relative paths for all paths in pathset"""
    return [relpath(p, frompath) for p in pathset]


def statistics() -> Tuple[int, int]:
    """Return file stat cache statistics: (hit-count, miss-count)."""
    return _stat_cnt["hit"], _stat_cnt["miss"]


def clear() -> None:
    """Clear path caches and default root and anchor paths"""
    global _root, _anchor, _cwd
    _stat_cache.clear()
    _stat_cnt.update({"hit": 0, "miss": 0})
    _dir_cache.clear()
    _explist_cache.clear()
    _root = None
    _anchor = None
    _cwd = normpath(abspath(getcwd()))
