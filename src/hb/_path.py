"""
Cononical file paths with caching
"""

import os
import re
from os.path import normpath, dirname, relpath
from os import getcwd
from stat import S_ISDIR
from typing import Dict, Iterable, List, Tuple, Union, Any
from dataclasses import dataclass, field


PathSet = Dict[str, bool]
AnyPath = Union[str, PathSet, Iterable[str], Iterable[Union[PathSet, str]]]
Context = Dict[str, Any]


@dataclass
class _Context:
    root: str
    cwd: str
    anchor: str = ""
    hits: int = 0
    misses: int = 0
    _explist_cache: Dict[str, PathSet] = field(default_factory=dict)
    _dir_cache: Dict[str, str] = field(default_factory=dict)
    _stat_cache: Dict[str, os.stat_result] = field(default_factory=dict)


def _normpath(path):
    """Return normalized absolute path"""
    path = normpath(path)
    # Handle special cases not covered by normpath:
    if path.endswith("/,"):
        path = path[:-2]
    if path.startswith("//"):
        path = path[1:]
    return path


def _find_root(path: str) -> str:
    parts = path.split("/")
    while parts:
        root = "/".join(parts)
        if os.path.exists(f"{root}/.hbroot"):
            return normpath(root)
        parts = parts[:-1]
    raise FileNotFoundError(f"Cannot find root given {path}")


def context(path: str = "", cls=_Context) -> _Context:
    """Create context based on given path, or current work directory
    if not given.  Return path conext"""
    path = _normpath(path or getcwd())
    return cls(
        root=_find_root(path),
        cwd=path,
        anchor=path,
    )


def canonical(context: _Context, path: str) -> str:
    """Return canonical absolute path given a relative or absolute path
    and a path context.
    Relative paths are relative context.anchor.
    Paths starting with $root/ are relative context.root.
    Surplus "/xxx/../", "/./", "//" etc are removed.
    Symlinks are not expanded.
    """
    if path[0] == "/":
        pass
    elif path.startswith("$root/"):
        path = path.replace("$root", context.root, 1)
    else:
        path = f"{context.anchor}/{path}"
    return _normpath(path)


def pathset(context: _Context, *paths: AnyPath) -> PathSet:
    """Create path set,
    Return a dict where the keys are canoical absolute paths.

    The insert order is preserved.
    For duplicates,  the first inserted is kept.
    """
    pset = dict()
    for path in paths:
        if isinstance(path, str):
            path = canonical(context, path)
            if path.endswith(".list"):
                pset.update(_explist(context, path))
            else:
                pset[path] = True
        elif isinstance(path, dict):
            pset.update(path)
        else:
            for p in path:
                pset.update(pathset(context, p))
    return pset


def paths(pathset: dict) -> Iterable[str]:
    """Return iterator for paths in pathset, in insertion order"""
    return pathset.keys()


_comment = re.compile(r"#.*$")


def _explist(context: _Context, listfilepath: str) -> PathSet:
    """Expand listfile (.list)
    Return pathset.
    """
    pset = context._explist_cache.get(listfilepath, {})
    if pset:
        return pset
    directory = dirname(listfilepath)
    anchor = context.anchor
    context.anchor = directory
    with open(listfilepath) as fh:
        for line in fh:
            line = _comment.sub("", line).strip()
            if not line:
                continue
            path = canonical(context, line)
            if path.endswith(".list"):
                pset.update(_explist(context, path))
            else:
                pset[path] = True
    context._explist_cache[listfilepath] = pset
    context.anchor = anchor
    return pset


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


def stat(context: _Context, path: str) -> os.stat_result:
    """Return, possibly cached, file stats for a path,
    or default statstics if the path does not exist.
    The default statistics represent a plain file with modification time
    zero.

    Use cache in context to only access the file system once per path.
    """
    fstat = context._stat_cache.get(path)
    if fstat is not None:
        context.hits += 1
        return fstat
    try:
        fstat = os.stat(path)
    except FileNotFoundError:
        fstat = _default_stat
    context._stat_cache[path] = fstat
    context.misses += 1
    return fstat


def isdir(context: _Context, path: str) -> bool:
    """Return True if path is a directory, False otherwise, usees
    path stat cache"""
    return S_ISDIR(stat(context, path).st_mode)


def exists(context: _Context, path: str) -> bool:
    """Return True if path exists, False otherwise, usees
    path stat cache"""
    return stat(context, path).st_ctime != 0


def newest(context: _Context, pathset: PathSet) -> str:
    """Return newest path in pathset"""
    return max(pathset, key=lambda x: stat(context, x).st_mtime)


def oldest(context: _Context, pathset: PathSet) -> str:
    """Return oldest path in pathset"""
    return min(pathset, key=lambda x: stat(context, x).st_mtime)


def directories(context: _Context, pathset: PathSet) -> PathSet:
    """Return directory part of all paths in pathset"""
    pset = {}
    for path in pathset:
        p = context._dir_cache.get(path)
        if not p:
            if isdir(context, path):
                p = path
            else:
                p = dirname(path)
            context._dir_cache[path] = p
        pset[p] = True
    return pset


def files(context: _Context, pathset: PathSet) -> PathSet:
    """Return all files in pathset. I.e. skip directories"""
    return {path: True for path in pathset if not isdir(context, path)}


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
