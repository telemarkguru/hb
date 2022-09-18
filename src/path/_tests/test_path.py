from .. import path

import os
import os.path as op

_this = op.normpath(op.abspath(op.dirname(__file__)))


def _expected_paths(*paths):
    return [f"{_this}/{x}" for x in paths]


def _assert_paths(pathset, expected):
    paths = list(path.paths(pathset))
    expected = _expected_paths(*expected)
    assert paths == expected


def test_root():
    pset = path.pathset(".", anchor=_this)
    assert path.root == _this
    assert list(path.paths(pset)) == [_this]


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


def test_cwd_use():
    cwd = os.getcwd()
    os.chdir(f"{_this}/files/subdir")
    pset = path.pathset(",")
    os.chdir(cwd)
    _assert_paths(pset, [f"files/subdir"])


def test_newest():
    path.clear()
    assert path._stat_cnt["hit"] == 0
    assert path._stat_cnt["miss"] == 0
    assert path._stat_cache == {}
    pset = path.pathset(f"/files/test1.list", anchor=_this)
    with open(f"{_this}/files/subdir2/foo/x.y", "w"):
        pass
    assert path.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert path._stat_cnt["hit"] == 0
    assert path._stat_cnt["miss"] == len(pset)
    with open(f"{_this}/files/subdir2/bar/a.file", "w"):
        pass
    assert path.newest(pset) == f"{_this}/files/subdir2/foo/x.y"
    assert path._stat_cnt["hit"] == len(pset)
    assert path._stat_cnt["miss"] == len(pset)
    path.clear()
    assert path._stat_cache == {}
    assert path.newest(pset) == f"{_this}/files/subdir2/bar/a.file"
