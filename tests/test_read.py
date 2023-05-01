import hb
from hb import path
from hb import read

import os.path as op


_this = op.normpath(op.abspath(op.dirname(__file__)))


def test_load():
    file = f"{_this}/files/hb.py"
    mod = read.load(file)
    assert mod.name == "foo.bar.x"
    assert mod.__file__.replace(".pyx", ".py") == file


def test_scan():
    context = hb.context(_this)
    pset = context.pathset("files/@test2")
    files, scanned = read.scan(path.directories(context, pset))
    assert list(files.keys()) == [
        f"{_this}/files/hb.py",
        f"{_this}/files/subdir/hb.py",
        f"{_this}/files/subdir2/foo/hb.py",
        f"{_this}/files/subdir2/bar/hb.py",
    ]
    assert list(scanned.keys()) == [
        f"{_this}/files",
        f"{_this}/files/subdir",
        f"{_this}/files/subdir2/foo",
        f"{_this}/files/subdir2/bar",
        f"{_this}/files/nonexistent/directory",
        f"{_this}/files/nonexistent",
    ]
