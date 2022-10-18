import hb

import os.path as op
import pytest


_this = op.normpath(op.abspath(op.dirname(__file__)))


def test_load():
    mod = hb.load(f"{_this}/files/hb.py")
    assert mod.name == "foo.bar.x"


def test_scan():
    pset = hb.pathset("files/test2.list", anchor=_this)
    hb.clear()
    hb.scan(hb.directories(pset))
    assert hb.loaded_files() == [f"{_this}/files/hb.py"]
