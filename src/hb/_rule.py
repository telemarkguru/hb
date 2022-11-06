from typing import Dict, Callable, Union, List
from string import Template
from dataclasses import dataclass
import sys
from ._path import PathSet, pathset, AnyPath, directories, relative, cwd
from ._read import scan


@dataclass
class _Rule:
    name: str
    command: str
    func: Callable = lambda: None
    used: bool = False


@dataclass
class _Build:
    rule: str
    dst: PathSet
    src: PathSet
    deps: PathSet
    oodeps: PathSet
    vars: dict
    callback: Union[Callable, None]


_rules: Dict[str, _Rule] = {}
targets: PathSet = {}
_builds: List[_Build] = []


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
        rule = _Rule(funcname, command)

        def func(*args, **kwargs):
            rule.used = True
            return function(*args, **kwargs)

        func.__doc__ = function.__doc__
        func.__name__ = funcname
        rule.func = func
        if funcname in _rules:
            raise KeyError(f"Rule {funcname} already defined")
        _rules[funcname] = rule
        setattr(sys.modules["hb"], funcname, func)

        return func

    return f


def _mange_path(path):
    return path.replace('/', '__').replace('..', 'up')


def build(
    function: Callable,
    dst: AnyPath = {},
    src: AnyPath = {},
    deps: AnyPath = {},
    oodeps: AnyPath = {},
    depfile: bool = False,
    callback: Union[Callable, None] = None,
    **vars: Dict[str, str],
) -> None:
    """Create build for rule
    Called from rule function. Arguments:

        function: a rule function (decorated by the rule() function)
        dst: Targets
        src; Dependencies
        deps: Indirect dependencies
        oodeps: Order only dependencies
        depfile: Use optional lazy dependency file (True or False)
        callback: Optional function that can add to oodeps after
                  all build calls have been processed.
                  The function shall return a pathset and take no arguments.
        **vars: variables to be expanded in the rule command string
    """
    dst = pathset(dst)
    src = pathset(src)
    deps = pathset(deps)
    oodeps = pathset(oodeps)
    if depfile:
        first = relative(cwd(), dst)[0]
        vars["depfile"] = ".hb/" + _mange_path(f"{first}.d")
    targets.update(dst)
    _builds.append(
        _Build(function.__name__, dst, src, deps, oodeps, vars, callback)
    )
    scan(directories({**src, **deps, **oodeps}))


def rules():
    """Iterate over all available rules, and yield
    (name, documentation) for each rule."""
    for name in _rules:
        yield name, _rules[name].func.__doc__


def clear():
    _rules.clear()
    targets.clear()
    _builds.clear()
