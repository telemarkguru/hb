import hb

import os
import os.path as op
import pytest

_this = op.normpath(op.abspath(op.dirname(__file__)))


def _compare_exp(file):
    with open(file) as fha, open(f"{file}.exp") as fhe:
        assert fha.read() == fhe.read()


def test_rule_define():
    hb.clear()
    hb.anchor(_this)

    @hb.rule("cat $in > $out")
    def test_nada():
        """
        Documentation
        """
        hb.build(test_nada, "a")
        return 42

    for rule in hb.rules():
        assert rule.name == "test_nada"
        assert rule.doc.strip() == "Documentation"

    assert hb.test_nada() == 42
    assert hb.targets == {f"{_this}/a": True}
    assert hb._rule._builds[0].rule == "test_nada"


def test_depfile():
    os.chdir(_this + "/..")
    hb.clear()
    hb.anchor(_this)

    @hb.rule("cat $in > $out")
    def depfile():
        hb.build(depfile, "foo", depfile=True)

    depfile()
    # assert hb._rule._builds[0].vars["depfile"] == ".hb/tests__foo.d"


def test_rule_redefine():
    hb.clear()

    @hb.rule("foo")
    def foo():
        pass

    hb.foo()

    with pytest.raises(KeyError, match=r"Rule foo already defined"):
        hb.rule("bar")(foo)


def test_write_ninja():
    os.chdir(_this)
    hb.clear()
    hb.anchor(_this)

    @hb.rule(
        "gcc -MM $depfile -c ${opts} -o $out $in", depfile=True, opts="-O2"
    )
    def gcc(*cfiles):
        cfiles = hb.pathset(*cfiles)
        for file in cfiles:
            hb.build(gcc, f"{file}.o", file)

    gcc("a.c", "b.c", "../d/c.c")
    ninja = f"{_this}/build.ninja"
    with open(ninja, "w") as fh:
        hb.write_ninja(fh)
    _compare_exp(ninja)


def test_pool():
    os.chdir(_this)
    hb.clear()
    hb.anchor(_this)

    @hb.rule(
        "echo hello >$out && cat $in >>$out",
        maxpar=2,
    )
    def hello(*files):
        files = hb.pathset(files)
        for file in files:
            hb.build(hello, f"{file}.hello", file)

    hello("files/hb.py")
    ninja = f"{_this}/build2.ninja"
    with open(ninja, "w") as fh:
        hb.write_ninja(fh)
    _compare_exp(ninja)
