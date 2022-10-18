from hb import read, path

import os.path as op
import pytest


_this = op.normpath(op.abspath(op.dirname(__file__)))


def test_load():
    mod = read.load(f"{_this}/files/hb.py")
    assert mod.name == "foo.bar.x"


def test_scan():
    pset = path.pathset("files/test2.list", anchor=_this)
    read.clear()
    read.scan(path.directories(pset))
    assert read.loaded_files() == [f"{_this}/files/hb.py"]
