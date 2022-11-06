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

    for name, doc in hb.rules():
        assert name == "test_nada"
        assert doc.strip() == "Documentation"

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
    assert hb._rule._builds[0].vars["depfile"] == ".hb/tests__foo.d"



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
