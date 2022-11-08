import hb

import os
import os.path as op
import pytest

_this = op.normpath(op.abspath(op.dirname(__file__)))


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
        @hb.rule("foo")
        def foo():
            pass


def test_write_ninja():
    os.chdir(_this)
    hb.clear()
    hb.anchor(_this)

    @hb.rule("gcc -MM $depfile -c ${opts} -o $out $in", depfile=True, opts="-O2")
    def gcc(*cfiles):
        cfiles = hb.pathset(*cfiles)
        for file in cfiles:
            hb.build(gcc, f"{file}.o", file)

    gcc("a.c", "b.c", "../d/c.c")
    with open(f"{_this}/build.ninja", "w") as fh:
        hb.write_ninja(fh)
