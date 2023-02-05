from hb import read as hb
from hb import path

import os.path as op


_this = op.normpath(op.abspath(op.dirname(__file__)))


def test_load():
    file = f"{_this}/files/hb.py"
    mod = hb.load(file)
    assert mod.name == "foo.bar.x"
    assert mod.__file__.replace(".pyx", ".py") == file


def test_scan():
    context = path.context(_this)
    pset = path.pathset(context, "files/test2.list")
    files, scanned = hb.scan(path.directories(context, pset))
    assert list(files.keys()) == [
        f"{_this}/files/hb.py",
        f"{_this}/files/subdir/hb.py",
    ]
    assert list(scanned.keys()) == [
        f"{_this}/files",
        f"{_this}/files/subdir",
        f"{_this}/files/subdir2/foo",
        f"{_this}/files/subdir2",
        f"{_this}/files/subdir2/bar",
        f"{_this}/files/nonexistent/directory",
        f"{_this}/files/nonexistent",
    ]
