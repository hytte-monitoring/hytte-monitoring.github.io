"""A scenario's function trace -> the implemented sequence diagram.

extract() runs the scenario executable of the traced build (core/trace.py records every
function entry and exit) and reads the messages off the trace, applying the sequence-diagram
rules of docs/UML-CPP-MAPPING.md mechanically:

    a message      the entry of a method of one of the project's classes, made while the
                   scenario's `scenario()` function runs
    its receiver   that class (the object's actual class, whatever the static type)
    its caller     the class of the nearest enclosing project method on the call stack —
                   code inside a lambda counts as the method it is written in — or the
                   initiator when the call comes from outside every class
    not messages   constructors, destructors, operators, free functions, the standard library

Objects are told apart by class, so one lifeline per class.
"""
from ..core import trace


def extract(executable, trace_path, classes, initiator):
    """-> (scenario, warnings). classes: the project's class names; initiator: the design's
    initiating lifeline, {"name", "kind"}."""
    warnings = []
    run = trace.record(executable, trace_path)
    if run.returncode != 0:
        tail = (run.stderr.strip().splitlines() or run.stdout.strip().splitlines() or [""])[-1]
        warnings.append(f"the scenario exited with code {run.returncode}"
                        + (f": {tail}" if tail else "") + "; the trace up to that point was read")
    if not trace_path.exists():
        raise RuntimeError(f"the scenario wrote no trace ({trace_path}); was it built with tracing?")

    events = trace.events(executable, trace_path)
    known = set(classes)
    messages, seen = _messages(events, known, initiator["name"], scenario_only=True)
    if not seen:
        warnings.append("no function named scenario() ran, so every call made from main() was counted")
        messages, _ = _messages(events, known, initiator["name"], scenario_only=False)

    lifelines = [dict(initiator)]
    for m in messages:
        for name in (m["from"], m["to"]):
            if all(l["name"] != name for l in lifelines):
                lifelines.append({"name": name, "kind": "object"})
    return {"lifelines": lifelines, "messages": messages}, warnings


def frame(name, known):
    """What one traced function is: its class and method, whether it is a message."""
    comps = trace.parts(name) if name else []
    f = {"class": None, "method": None, "message": False, "scenario": bool(comps) and comps[-1] == "scenario"}
    for k, comp in enumerate(comps):
        if comp in known:
            f["class"] = comp
            if k + 1 < len(comps):
                method = comps[k + 1]
                nested = k + 2 < len(comps)              # a lambda or local class inside the method
                special = method == comp or method.startswith("~") or method.startswith("operator")
                f["method"] = method
                f["message"] = not nested and not special
            break
    return f


def _messages(events, known, initiator, scenario_only):
    """Walk the entries and exits -> ([message], whether scenario() was seen)."""
    stack, messages = [], []
    inside, seen = not scenario_only, False
    for kind, addr, name in events:
        if kind == "E":
            f = {**frame(name, known), "addr": addr}
            if f["scenario"] and scenario_only and not inside:
                inside, seen = True, True
            elif inside and f["message"]:
                caller = next((s["class"] for s in reversed(stack) if s["class"]), None) or initiator
                messages.append({"from": caller, "to": f["class"], "name": f["method"],
                                 "text": f"{f['method']}()", "kind": "call"})
            stack.append(f)
        else:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i]["addr"] == addr:
                    if stack[i]["scenario"] and scenario_only:
                        inside = False
                    del stack[i:]
                    break
    return messages, seen
