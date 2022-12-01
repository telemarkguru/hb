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
    pset = hb.pathset("$root/files/test1.list", anchor=_this)
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
    hb.clear()
    hb.anchor(_this)
    pset1 = hb.pathset("files")
    pset2 = hb.pathset("$root/files/subdir2/foo/foo.list")
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
    hb.clear()
    hb.anchor(hb.cwd())
    pset = hb.pathset(",")
    os.chdir(cwd)
    _assert_paths(pset, ["files/subdir"])


def _touch(path):
    if op.exists(path):
        os.unlink(path)
    with open(path, "w") as fh:
        fh.write("x")


def test_newest():
    hb.clear()
    assert hb.statistics() == (0, 0)
    hb.clear()
    n1 = f"{_this}/onew.txt"
    n2 = f"{_this}/newest.txt"
    _touch(n1)
    _touch(n2)
    pset = hb.pathset(
        "$root/files/test1.list", n1, n2, anchor=_this
    )
    assert hb.newest(pset) == n2
    assert hb.statistics() == (0, len(pset))
    _touch(n1)
    assert hb.newest(pset) == n2
    assert hb.statistics() == (len(pset), len(pset))
    hb.clear()
    assert hb.statistics() == (0, 0)
    assert hb.newest(pset) == n1


def test_oldest():
    hb.clear()
    n1 = f"{_this}/onew.txt"
    pset = hb.pathset("$root/files/subdir2/bar/files.list", n1, anchor=_this)
    for p in ("bar/a.file", "foo/z.w"):
        _touch(f"{_this}/files/subdir2/{p}")
    _touch(n1)
    assert hb.oldest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert hb.newest(pset) == n1


def test_directories():
    hb.clear()
    pset = hb.pathset(
        "$root/files/test1.list",
        "files/subdir2",
        "files/dirsymlink",
        anchor=_this,
    )
    directories = hb.directories(pset)
    _assert_paths(
        directories,
        [
            "files",
            "files/subdir",
            "files/subdir2/foo",
            "files/subdir2/bar",
            "files/subdir2",
            "files/dirsymlink",
        ],
    )


def test_files():
    hb.clear()
    pset = hb.pathset(
        "$root/files/test1.list",
        "files/dirsymlink",
        "files/slink",
        anchor=_this,
    )
    _assert_paths(
        hb.files(pset),
        [
            "files/foo.bar",
            "files/subdir/foo.bar",
            "files/bar.foo",
            "files/subdir2/foo/x.y",
            "files/subdir2/bar/a.file",
            "files/subdir2/foo/z.w",
            "files/slink",
        ],
    )


def test_filter():
    hb.clear()
    pset = hb.pathset("$root/files/test1.list", anchor=_this)
    foo = hb.filter(pset, r"/foo/")
    _assert_paths(
        foo,
        [
            "files/subdir2/foo/x.y",
            "files/subdir2/foo/z.w",
        ],
    )
    foo, bar = hb.filter(pset, r"/foo/", r"\.bar$")
    _assert_paths(
        foo,
        [
            "files/subdir2/foo/x.y",
            "files/subdir2/foo/z.w",
        ],
    )
    _assert_paths(bar, ["files/foo.bar", "files/subdir/foo.bar"])


def test_relative():
    hb.clear()
    pset = hb.pathset("$root/files/test1.list", anchor=_this)
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
    p, *_ = hb.paths(hb.pathset(f"/{_this}/files/test1.list", anchor=_this))
    assert not hb.exists("/a/file/that/does/not/exist")
    assert hb.exists(p)
    # Try again, to make sure cached values are working
    assert not hb.exists("/a/file/that/does/not/exist")
    assert hb.exists(p)
