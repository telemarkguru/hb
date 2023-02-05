import hb

import os
import os.path as op
import pytest

_this = op.normpath(op.abspath(op.dirname(__file__)))


def _compare_exp(file):
    with open(file) as fha, open(f"{file}.exp") as fhe:
        assert fha.read() == fhe.read()


def test_rule_define():
    context = hb.context(_this)

    @context.rule("cat $in > $out")
    def test_nada():
        """
        Documentation
        """
        context.build(test_nada, "a")
        return 42

    for rule in context.rules():
        assert rule.name == "test_nada"
        assert rule.doc.strip() == "Documentation"

    assert context.test_nada() == 42
    assert context.targets == {f"{_this}/a": True}
    assert context._builds[0].rule == "test_nada"


def test_depfile():
    os.chdir(_this + "/..")
    context = hb.context(_this)

    @context.rule("cat $in > $out")
    def depfile():
        context.build(depfile, "foo", depfile=True)

    depfile()
    # assert hb._rule._builds[0].vars["depfile"] == ".hb/tests__foo.d"


def test_rule_redefine():
    context = hb.context(_this)

    @context.rule("foo")
    def foo():
        pass

    context.foo()

    with pytest.raises(KeyError, match=r"Name foo already defined"):
        context.rule("bar")(foo)


def test_write_ninja():
    os.chdir(_this)
    context = hb.context(_this)

    @context.rule(
        "gcc -MM $depfile -c ${opts} -o $out $in", depfile=True, opts="-O2"
    )
    def gcc(*cfiles):
        cfiles = context.pathset(*cfiles)
        for file in cfiles:
            context.build(gcc, f"{file}.o", file)

    gcc("a.c", "b.c", "../d/c.c")
    ninja = f"{_this}/build.ninja"
    with open(ninja, "w") as fh:
        context.write_ninja(fh)
    _compare_exp(ninja)


def test_pool():
    os.chdir(_this)
    context = hb.context()

    @context.rule(
        "echo hello >$out && cat $in >>$out",
        maxpar=2,
        deps=f"{_this}/files/subdir/foo.bar",
    )
    def hello(*files):
        files = context.pathset(files)
        for file in files:
            context.build(hello, f"{file}.hello", file)

    hello("files/hb.py")
    ninja = f"{_this}/build2.ninja"
    with open(ninja, "w") as fh:
        context.write_ninja(fh)
    _compare_exp(ninja)


def test_build_scan():
    context = hb.context(_this)

    @context.rule("cat $in >$out")
    def scanner(outfile, *infiles):
        context.build(
            scanner, context.pathset(outfile), context.pathset(*infiles)
        )

    scanner(f"{_this}/files/floppy.txt", f"{_this}/files/test1.list")
    assert context.floppydisk == 3
    assert context.subdir
