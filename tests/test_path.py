import hb
from hb import path

import os
import os.path as op
import pytest
import time


_this = op.normpath(op.abspath(op.dirname(__file__)))


def _expected_paths(*paths):
    return [f"{_this}/{x}" for x in paths]


def _assert_paths(pathset, expected):
    paths = list(path.paths(pathset))
    expected = _expected_paths(*expected)
    assert paths == expected


def test_root():
    context = hb.context(f"{_this}/subdir")
    pset = context.pathset(".")
    assert context.root == _this
    assert list(context.paths(pset)) == [f"{_this}/subdir"]
    with pytest.raises(FileNotFoundError, match=r"Cannot find root.*"):
        hb.context(f"{_this}/..")


def test_pathset():
    context = hb.context(_this)
    pset = context.pathset("$root/files/@test1")
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
    context = hb.context(_this)
    pset1 = context.pathset("files")
    pset2 = context.pathset("$root/files/subdir2/foo/@foo")
    pset = context.pathset(pset1, pset2, ["files/subdir", "files/foo.bar"])
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
    context = hb.context()
    pset = context.pathset(",")
    os.chdir(cwd)
    _assert_paths(pset, ["files/subdir"])


def _touch(path):
    if op.exists(path):
        os.unlink(path)
    with open(path, "w") as fh:
        fh.write("x")
    t0 = os.stat(path).st_mtime_ns
    while True:
        with open(path, "w") as fh:
            fh.write("x")
        t1 = os.stat(path).st_mtime_ns
        if t1 > t0:
            return
        time.sleep(1)


def test_newest():
    context = hb.context(_this)
    assert context.misses == 0
    assert context.hits == 0
    n1 = f"{_this}/onew.txt"
    n2 = f"{_this}/newest.txt"
    _touch(n1)
    _touch(n2)
    pset = context.pathset("$root/files/@test1", n1, n2)
    assert context.newest(pset) == n2
    assert context.hits == 0
    assert context.misses == len(pset)
    _touch(n1)
    assert context.newest(pset) == n2
    assert context.hits == len(pset)
    assert context.misses == len(pset)
    context = hb.context(_this)
    assert context.misses == 0
    assert context.hits == 0
    assert context.newest(pset) == n1


def test_oldest():
    context = hb.context(_this)
    n1 = f"{_this}/onew.txt"
    pset = context.pathset("$root/files/subdir2/bar/@files", n1)
    for p in ("bar/a.file", "foo/z.w"):
        _touch(f"{_this}/files/subdir2/{p}")
    _touch(n1)
    assert context.oldest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert context.newest(pset) == n1


def test_directories():
    context = hb.context(_this)
    pset = context.pathset(
        "$root/files/@test1",
        "files/subdir2",
        "files/dirsymlink",
    )
    directories = context.directories(pset)
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
    context = hb.context(_this)
    pset = context.pathset(
        "$root/files/@test1",
        "files/dirsymlink",
        "files/slink",
    )
    _assert_paths(
        context.files(pset),
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
    context = hb.context(_this)
    pset = context.pathset("$root/files/@test1")
    foo = context.filter(pset, r"/foo/")
    _assert_paths(
        foo,
        [
            "files/subdir2/foo/x.y",
            "files/subdir2/foo/z.w",
        ],
    )
    foo, bar = context.filter(pset, r"/foo/", r"\.bar$")
    _assert_paths(
        foo,
        [
            "files/subdir2/foo/x.y",
            "files/subdir2/foo/z.w",
        ],
    )
    _assert_paths(bar, ["files/foo.bar", "files/subdir/foo.bar"])


def test_relative():
    context = hb.context(_this)
    pset = context.pathset("$root/files/@test1")
    rp = context.relative(f"{_this}/files/subdir/ping", pset)
    assert rp == [
        "../../foo.bar",
        "../foo.bar",
        "../../bar.foo",
        "../../subdir2/foo/x.y",
        "../../subdir2/bar/a.file",
        "../../subdir2/foo/z.w",
    ]


def test_exists():
    context = hb.context(_this)
    p, *_ = context.paths(context.pathset(f"/{_this}/files/@test1"))
    assert not context.exists("/a/file/that/does/not/exist")
    assert context.exists(p)
    # Try again, to make sure cached values are working
    assert not context.exists("/a/file/that/does/not/exist")
    assert context.exists(p)
