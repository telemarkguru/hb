from . import _path as path
from . import _read as read
from . import _rule as rule


class Context(rule._Context):

    pathset = path.pathset
    export = path.export
    canonical = path.canonical
    stat = path.stat
    isdir = path.isdir
    exists = path.exists
    newest = path.newest
    oldest = path.oldest
    directories = path.directories
    files = path.files

    build = rule.build
    rules = rule.rules
    write_ninja = rule.write_ninja
    rule = rule.rule

    def paths(self, pathset):
        return path.paths(pathset)

    def filter(self, pathset, *patterns):
        return path.filter(pathset, *patterns)

    def relative(self, frompath, pathset):
        return path.relative(frompath, pathset)


def context(cwdpath: str = ""):
    """Create context base on given path, or current directory
    if not given, Return rule context"""
    return path.context(cwdpath, Context)


__all__ = [
    "path",
    "read",
    "rule",
    "Context",
]
