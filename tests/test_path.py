import hb

import os
import os.path as op
import pytest


_this = op.normpath(op.abspath(op.dirname(__file__)))


def _expected_paths(*paths):
    return [f"{_this}/{x}" for x in paths]


def _assert_paths(pathset, expected):
    paths = list(hb.paths(pathset))
    expected = _expected_paths(*expected)
    assert paths == expected


def test_root():
    pset = hb.pathset(".", anchor=f"{_this}/subdir")
    assert hb.root() == _this
    assert list(hb.paths(pset)) == [f"{_this}/subdir"]
    hb.clear()
    with pytest.raises(FileNotFoundError, match=r"Cannot find root.*"):
        pset = hb.pathset(".", anchor=op.normpath(f"{_this}/.."))


def test_pathset():
    pset = hb.pathset("/files/test1.list", anchor=_this)
    _assert_paths(
        pset,
        [
            "files/foo.bar",
            "files/subdir/foo.bar",
            "files/bar.foo",
            "files/subdir2/foo/x.y",
            "files/subdir2/bar/a.file",
            "files/subdir2/foo/z.w",
        ],
    )


def test_merge_pathsets():
    hb.anchor(_this)
    pset1 = hb.pathset("files")
    pset2 = hb.pathset("/files/subdir2/foo/foo.list")
    pset = hb.pathset(pset1, pset2, ["files/subdir", "files/foo.bar"])
    _assert_paths(
        pset,
        [
            "files",
            "files/subdir2/foo/z.w",
            "files/subdir",
            "files/foo.bar",
        ],
    )


def test_cwd_use():
    cwd = os.getcwd()
    os.chdir(f"{_this}/files/subdir")
    hb.anchor(hb.cwd())
    pset = hb.pathset(",")
    os.chdir(cwd)
    _assert_paths(pset, ["files/subdir"])


def test_newest():
    hb.clear()
    assert hb.statistics() == (0, 0)
    hb.clear()
    pset = hb.pathset("/files/test1.list", anchor=_this)
    with open(f"{_this}/files/subdir2/foo/x.y", "w"):
        pass
    assert hb.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert hb.statistics() == (0, len(pset))
    with open(f"{_this}/files/subdir2/bar/a.file", "w"):
        pass
    assert hb.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert hb.statistics() == (len(pset), len(pset))
    hb.clear()
    assert hb.statistics() == (0, 0)
    assert hb.newest(pset) == f"{_this}/files/subdir2/bar/a.file"


def test_oldest():
    hb.clear()
    pset = hb.pathset("/files/subdir2/bar/files.list", anchor=_this)
    for p in ("bar/a.file", "foo/z.w"):
        with open(f"{_this}/files/subdir2/{p}", "w"):
            pass
    assert hb.oldest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert hb.newest(pset) == f"{_this}/files/subdir2/foo/z.w"


def test_directories():
    hb.clear()
    pset = hb.pathset("/files/test1.list", "files/subdir2", anchor=_this)
    directories = hb.directories(pset)
    _assert_paths(
        directories,
        [
            "files",
            "files/subdir",
            "files/subdir2/foo",
            "files/subdir2/bar",
            "files/subdir2",
        ],
    )


def test_relative():
    hb.clear()
    pset = hb.pathset("/files/test1.list", anchor=_this)
    rp = hb.relative(f"{_this}/files/subdir/ping", pset)
    assert rp == [
        "../../foo.bar",
        "../foo.bar",
        "../../bar.foo",
        "../../subdir2/foo/x.y",
        "../../subdir2/bar/a.file",
        "../../subdir2/foo/z.w",
    ]


def test_exists():
    hb.clear()
    p, *_ = hb.paths(hb.pathset("/files/test1.list", anchor=_this))
    assert not hb.exists("/a/file/that/does/not/exist")
    assert hb.exists(p)
    # Try again, to make sure cached values are working
    assert not hb.exists("/a/file/that/does/not/exist")
    assert hb.exists(p)
