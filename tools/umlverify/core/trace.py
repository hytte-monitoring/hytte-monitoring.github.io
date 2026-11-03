"""Function traces of an instrumented program: recording them and resolving them to names.

The sequence-diagram flow builds a project a second time with every function compiled with
entry/exit hooks (see runtime/instrument.cmake and runtime/uml_trace.cpp), runs a scenario
executable with UML_TRACE_FILE set, and turns the recorded addresses back into function names
with the executable's own symbol table (nm). This module is diagram-agnostic: it yields entries
and exits with demangled names; what they mean is the flow's business.
"""
import os
import re
import subprocess
from pathlib import Path

REFERENCE = "uml_trace_reference"       # the runtime's anchor symbol; undoes address randomisation


def record(executable, trace_path, timeout=60):
    """Run the executable with tracing on. Returns the CompletedProcess (never raises on a
    non-zero exit; a missing executable raises FileNotFoundError)."""
    Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "UML_TRACE_FILE": str(trace_path)}
    return subprocess.run([str(executable)], env=env, capture_output=True, text=True,
                          timeout=timeout, cwd=str(Path(executable).parent))


def _scan(executable):
    """[(address, demangled name)] for every defined symbol of the executable, in nm order."""
    for args in (["nm", "-n", "--demangle"], ["nm", "-n"]):
        run = subprocess.run(args + [str(executable)], capture_output=True, text=True,
                             errors="replace")
        if run.returncode == 0:
            break
    else:
        raise RuntimeError("nm could not read the executable's symbols: " + run.stderr.strip())
    found = []
    for line in run.stdout.splitlines():
        m = re.match(r"^([0-9a-fA-F]+)\s+(\S)\s+(.+)$", line)
        if m and m.group(2) not in "Uu":
            found.append((int(m.group(1), 16), m.group(3)))
    if "--demangle" not in args:                      # older nm: demangle in one go
        run = subprocess.run(["c++filt"], input="\n".join(n for _, n in found) + "\n",
                             capture_output=True, text=True, errors="replace")
        if run.returncode == 0:
            found = [(a, n) for (a, _), n in zip(found, run.stdout.splitlines())]
    return found


def symbols(executable):
    """{address: demangled name} for every defined symbol of the executable. Several symbols
    can share an address (Windows nm also lists section symbols such as ".text"): the first
    real function name wins."""
    return _table(_scan(executable))


def _table(scanned):
    table = {}
    for address, name in scanned:
        if address not in table or (table[address].startswith(".") and not name.startswith(".")):
            table[address] = name
    return table


def events(executable, trace_path):
    """The recorded trace -> [(kind, address, name)], kind "E" (entry) or "X" (exit); name is
    None for an address the symbol table does not know."""
    scanned = _scan(executable)
    table = _table(scanned)
    reference = next((a for a, n in scanned if n.lstrip("_") == REFERENCE), None)
    out, slide = [], None
    for line in Path(trace_path).read_text().splitlines():
        kind, _, addr = line.partition(" ")
        if not addr:
            continue
        address = int(addr, 16)
        if kind == "R":
            slide = address - reference if reference is not None else 0
            continue
        if slide is None:
            slide = 0
        static = address - slide
        out.append((kind, static, table.get(static)))
    return out


def parts(demangled):
    """A demangled function name -> its qualified-name components, without template arguments,
    parameter lists, return types and qualifiers.

        'mini::Thermostat::setTarget(double)::$_0::operator()(int) const'
            -> ['mini', 'Thermostat', 'setTarget', '$_0', 'operator()']
        'void lib::Catalog<lib::Book>::add(lib::Book)' -> ['lib', 'Catalog', 'add']
    """
    s = (demangled or "").strip()
    s = re.sub(r"\s+(const|volatile|&&?|noexcept)$", "", s)
    s = re.sub(r"\s+(const|volatile|&&?|noexcept)$", "", s)
    s = _drop_trailing_group(s, "()")               # the parameter list
    tokens = _split_top(s, " ")                     # a return type comes first, as its own token
    name = tokens[-1] if tokens else s
    comps = []
    for comp in _split_top(name, "::"):
        if comp.startswith("operator"):
            comps.append(comp.strip())              # operator< is not a template
            continue
        comp = _drop_top_groups(comp, "<>")         # template arguments
        comp = re.sub(r"\[abi:[^\]]*\]", "", comp)
        comp = _drop_trailing_group(comp, "()")     # an enclosing function's parameters
        comp = comp.strip()
        if comp:
            comps.append(comp)
    return comps


_PAIRS = {"(": ")", "<": ">", "[": "]", "{": "}"}
_CLOSE = {v: k for k, v in _PAIRS.items()}


def _split_top(s, sep):
    """Split at sep outside any brackets."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(s):
        ch = s[i]
        if s.startswith(sep, i) and depth == 0:
            out.append(cur)
            cur = ""
            i += len(sep)
            continue
        if ch in _PAIRS and not (ch == "<" and s.startswith("<=", i)):
            depth += 1
        elif ch in _CLOSE and depth > 0:
            depth -= 1
        cur += ch
        i += 1
    out.append(cur)
    return [t for t in out if t != ""]


def _drop_trailing_group(s, pair):
    """'f(int, std::pair<a, b>)' -> 'f' when pair is '()'; nothing dropped if s does not end in one."""
    opener, closer = pair
    if not s.endswith(closer):
        return s
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        if s[i] == closer:
            depth += 1
        elif s[i] == opener:
            depth -= 1
            if depth == 0:
                return s[:i]
    return s


def _drop_top_groups(s, pair):
    """Remove every top-level bracketed group: 'Catalog<lib::Book>' -> 'Catalog'."""
    opener, closer = pair
    out, depth = "", 0
    for ch in s:
        if ch == opener:
            depth += 1
        elif ch == closer and depth > 0:
            depth -= 1
        elif depth == 0:
            out += ch
    return out
