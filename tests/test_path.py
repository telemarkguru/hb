from hb import path

import os
import os.path as op
import pytest


_this = op.normpath(op.abspath(op.dirname(__file__)))


def _expected_paths(*paths):
    return [f"{_this}/{x}" for x in paths]


def _assert_paths(pathset, expected):
    paths = list(path.paths(pathset))
    expected = _expected_paths(*expected)
    assert paths == expected


def test_root():
    pset = path.pathset(".", anchor=f"{_this}/subdir")
    assert path.root() == _this
    assert list(path.paths(pset)) == [f"{_this}/subdir"]
    path.clear()
    with pytest.raises(FileNotFoundError, match=r"Cannot find root.*"):
        pset = path.pathset(".", anchor=os.path.normpath(f"{_this}/.."))


def test_pathset():
    pset = path.pathset(f"/files/test1.list", anchor=_this)
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
    path.anchor(_this)
    pset1 = path.pathset(f"files")
    pset2 = path.pathset(f"/files/subdir2/foo/foo.list")
    pset = path.pathset(pset1, pset2, ["files/subdir", "files/foo.bar"])
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
    path.anchor(path.cwd())
    pset = path.pathset(",")
    os.chdir(cwd)
    _assert_paths(pset, [f"files/subdir"])


def test_newest():
    path.clear()
    assert path.statistics() == (0, 0)
    path.clear()
    pset = path.pathset(f"/files/test1.list", anchor=_this)
    with open(f"{_this}/files/subdir2/foo/x.y", "w"):
        pass
    assert path.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert path.statistics() == (0, len(pset))
    with open(f"{_this}/files/subdir2/bar/a.file", "w"):
        pass
    assert path.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert path.statistics() == (len(pset), len(pset))
    path.clear()
    assert path.statistics() == (0, 0)
    assert path.newest(pset) == f"{_this}/files/subdir2/bar/a.file"


def test_oldest():
    path.clear()
    pset = path.pathset("/files/subdir2/bar/files.list", anchor=_this)
    for p in ("bar/a.file", "foo/z.w"):
        with open(f"{_this}/files/subdir2/{p}", "w"):
            pass
    assert path.oldest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert path.newest(pset) == f"{_this}/files/subdir2/foo/z.w"


def test_directories():
    path.clear()
    pset = path.pathset(f"/files/test1.list", "files/subdir2", anchor=_this)
    directories = path.directories(pset)
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
    path.clear()
    pset = path.pathset("/files/test1.list", anchor=_this)
    rp = path.relative(f"{_this}/files/subdir/ping", pset)
    assert rp == [
        "../../foo.bar",
        "../foo.bar",
        "../../bar.foo",
        "../../subdir2/foo/x.y",
        "../../subdir2/bar/a.file",
        "../../subdir2/foo/z.w",
    ]
