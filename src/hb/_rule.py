from typing import Dict, Callable, List, Tuple
from dataclasses import dataclass, field
import re
import ninja
from ._path import PathSet, pathset, AnyPath, directories, relative
from ._path import _Context as _PathContext
from ._read import scan, load


_CallBack = Callable[["_Context"], Tuple[PathSet, PathSet]]


def _default_callback(_: "_Context") -> Tuple[PathSet, PathSet]:
    return {}, {}


@dataclass
class _Rule:
    name: str
    command: str
    doc: str
    deps: PathSet
    oodeps: PathSet
    func: Callable = lambda: None
    used: bool = False
    pool: str = ""
    maxpar: int = 0
    vars: Dict[str, str] = field(default_factory=dict)
    callback: _CallBack = _default_callback


@dataclass
class _Build:
    rule: str
    dst: PathSet
    src: PathSet
    deps: PathSet
    oodeps: PathSet
    vars: Dict[str, str]


@dataclass
class _Context(_PathContext):
    _rules: Dict[str, _Rule] = field(default_factory=dict)
    targets: PathSet = field(default_factory=dict)
    _builds: List[_Build] = field(default_factory=list)
    _scanned: PathSet = field(default_factory=dict)


_var = re.compile(r"\$\{?(\w+)\}?")
_ninja_stdvar = set(
    (
        "in",
        "out",
        "depfile",
        "deps",
        "description",
        "generator",
        "pool",
        "restat",
        "rspfile",
        "rspfile_content",
    )
)


def rule(
    context: _Context,
    command: str,
    maxpar: int = 0,
    pool: str = "",
    deps: AnyPath = {},
    oodeps: AnyPath = {},
    callback: _CallBack = _default_callback,
    name: str = "",
    **vars: str,
) -> Callable[[Callable], Callable]:
    """Rule decorator, create a rule function
    Arguments:

        command: Command string, $-variables are expanded.
        maxpar: Maximum parallel runining processes of this rule.
                Default no limit.
        pool: Ninja pool. Default no pool.
        deps: Optional rule dependencies.
        oodpes: Optional rule order only dependencies.
        callback: Optional rule callback, called after all rules and
                  builds have been defined, if the rule is used.
                  The callback thakes a pathset with all targets,
                  and shall return one pathset for extra dependencies
                  and one pathset for extra order only dependencies.
        name: Optional rule name, if not given the function name is used.
        **vars: Optional default values for command variables.

        Standard variables in command string:
           $out - destination files/targets
           $in - direct dependencies
           $depfile - lazy dependencies file

        Other variables are axpanded if they are defined
        as keyword arguments to the build() function.
    """

    def f(function: Callable) -> Callable:
        funcname = name or function.__name__
        rule = _Rule(
            funcname,
            command,
            function.__doc__ or "",
            pathset(context, deps),
            pathset(context, oodeps),
        )

        def func(*args, **kwargs):
            rule.used = True
            return function(*args, **kwargs)

        func.__doc__ = function.__doc__
        func.__name__ = funcname
        rule.func = func
        rule.vars = vars
        rule.pool = pool
        rule.maxpar = maxpar
        if funcname in context._rules or getattr(context, funcname, False):
            raise KeyError(f"Name {funcname} already defined")
        context._rules[funcname] = rule
        setattr(context, funcname, func)

        return func

    return f


def _mangle_path(path):
    return path.replace("/", "__").replace("..", "up")


def build(
    context: _Context,
    function: Callable,
    dst: AnyPath = {},
    src: AnyPath = {},
    deps: AnyPath = {},
    oodeps: AnyPath = {},
    **vars: str,
) -> None:
    """Create build for rule
    Called from rule function. Arguments:

        function: a rule function (decorated by the rule() function)
        dst: Targets
        src; Dependencies
        deps: Indirect dependencies
        oodeps: Order only dependencies
        depfile: Use optional lazy dependency file (True or False)
        **vars: variables to be expanded in the rule command string
    """
    dst = pathset(context, dst)
    src = pathset(context, src)
    deps = pathset(context, deps)
    oodeps = pathset(context, oodeps)
    context.targets.update(dst)
    context._builds.append(
        _Build(function.__name__, dst, src, deps, oodeps, vars)
    )

    files, context._scanned = scan(
        directories(context, {**src, **deps, **oodeps}),
        "hb.py",
        context._scanned,
    )
    for file in files:
        mod = load(file)
        if hasattr(mod, "build"):
            mod.build(context)


def rules(context: _Context):
    """Iterate over all available rules,
    and yield a _Rule object for each rule
    """
    for name in context._rules:
        yield context._rules[name]


def _extract_cmd_vars(rule):
    vars = {}
    name = rule.name

    def repl(m):
        var = m[1]
        if var in _ninja_stdvar:
            return m[0]
        var = f"{name}_{var}"
        vars[var] = ""
        return f"${{{var}}}"

    for var in rule.vars:
        vars[f"{name}_{var}"] = rule.vars[var]

    return _var.sub(repl, rule.command), vars


def _write_rule(context: _Context, writer, rule):
    command, vars = _extract_cmd_vars(rule)
    for name in vars:
        writer.variable(name, vars[name])
    pool = rule.pool
    maxpar = rule.maxpar
    if maxpar:
        pool = f"{rule.name}_pool"
        writer.pool(pool, maxpar)
    edeps, eoodeps = rule.callback(context)
    rule.deps.update(edeps)
    rule.oodeps.update(eoodeps)
    writer.rule(
        rule.name,
        command,
        depfile=rule.vars.get("depfile"),
        pool=pool,
        generator=None,
    )
    writer.newline()


def _write_build(context: _Context, writer, build):
    cwd = context.cwd
    rule = context._rules[build.rule]
    dst = relative(cwd, build.dst)
    src = relative(cwd, build.src)
    deps = relative(cwd, {**build.deps, **rule.deps})
    oodeps = relative(cwd, {**build.oodeps, **rule.oodeps})
    vars = build.vars
    if rule.vars.get("depfile"):
        vars["depfile"] = ".hb/" + _mangle_path(f"{dst[0]}.d")
    writer.build(dst, build.rule, src, deps, oodeps, vars)
    if "/" not in dst[0]:
        writer.default(dst)


def write_ninja(context: _Context, fh):
    """Write ninja build file"""
    writer = ninja.Writer(fh)
    writer.variable("builddir", ".hb")
    for rule in context._rules.values():
        if rule.used:
            _write_rule(context, writer, rule)
    for build in context._builds:
        _write_build(context, writer, build)
