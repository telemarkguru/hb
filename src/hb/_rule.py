from typing import Dict, Callable
from string import Template
from dataclasses import dataclass
import sys
from ._path import PathSet, pathset, AnyPath


@dataclass
class _Rule:
    name: str
    command: str
    func: Callable
    used: bool = False


_rules: Dict[str, _Rule] = {}
targets: PathSet = {}


def rule(command: str) -> Callable[[Callable], Callable]:
    """Rule decorator, create a rule function
    Arguments:

        command: Command string, $-variables are expanded.

        Standard variables:
           $out - destination files/targets
           $in - direct dependencies

        Other variables are axpanded if they are defined
        as keyword arguments to the build() function.
    """

    def f(function: Callable) -> Callable:
        funcname = function.__name__

        def func(*args, **kwargs):
            func.used = True
            return function(*args, **kwargs)

        rule = _Rule(funcname, command, func)
        func.__doc__ = function.__doc__
        if funcname in _rules:
            raise KeyError(f"Rule {funcname} already defined")
        _rules[funcname] = rule
        setattr(sys.modules["hb"], funcname, func)

        return func

    return f


def build(
    function: Callable,
    dst: AnyPath = {},
    src: AnyPath = {},
    deps: AnyPath = {},
    oodeps: AnyPath = {},
    depsfile: str = "",
    **kwargs: Dict[str, str],
) -> None:
    """Create build for rule
    Called from rule function. Arguments:

        function: a rule function (decorated by the rule() function)
        dst: Targets
        src; Dependencies
        deps: Indirect dependencies
        oodeps: Order only dependencies
        depsfile: Optional lazy dependency file
        **kwargs: variables to be expanded in the rule command string
    """
    dst = pathset(dst)
    src = pathset(src)
    deps = pathset(deps)
    oodeps = pathset(oodeps)

    targets.update(dst)


def rules():
    """Iterate over all available rules, and yield
    (name, documentation) for each rule."""
    for name in _rules:
        yield name, _rules[name].func.__doc__


def clear():
    _rules.clear()
    targets.clear()
