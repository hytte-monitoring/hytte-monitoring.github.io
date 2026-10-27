"""Read and write the mermaid `stateDiagram-v2` subset used by the state-machine flow.

A machine is:

    {"states":      [name, ...]          in drawing / declaration order
     "initial":     name or None         the state the initial transition `[*] --> S` enters
     "transitions": [{"from", "event", "guard", "action", "to"}]
     "final":       [name, ...]}         states drawn with an edge to the end symbol, `S --> [*]`

Transition labels are written the UML way, `event [guard] / action`; guard and action
may be empty. Events are whatever the transitions use: events(machine) lists them in
order of first use. A state name may contain spaces in a drawing, but mermaid needs
an identifier, so such a state is written `state "Waiting for payment" as WaitingForPayment`.
"""
import re


def parse_label(text):
    """'event [guard] / action' -> (event, guard, action); each may be empty."""
    m = re.match(r"^\s*([^\[/]*?)\s*(?:\[\s*([^\]]*?)\s*\])?\s*(?:/\s*(.*?))?\s*$", text or "")
    if not m:
        return (text or "").strip(), "", ""
    event, guard, action = (g or "" for g in m.groups())
    event = re.sub(r"\s*\(.*\)\s*$", "", event)              # open(force) -> open
    return (event.strip(), re.sub(r"\(\s*\)$", "", guard).strip(),
            re.sub(r"\(\s*\)$", "", action).strip())


def label(t):
    """A transition's label as UML writes it: `event [guard] / action`."""
    out = t["event"]
    if t["guard"]:
        out += f" [{t['guard']}]"
    if t["action"]:
        out += f" / {t['action']}"
    return out.strip()


def state_id(name):
    """A mermaid identifier for a state name: 'Waiting for payment' -> 'WaitingForPayment'."""
    words = re.findall(r"[A-Za-z0-9_]+", name or "")
    ident = "".join(w if n == 0 else w[:1].upper() + w[1:] for n, w in enumerate(words))
    return ident or "State"


def events(machine):
    """The events the transitions use, in order of first use."""
    seen = []
    for t in machine["transitions"]:
        if t["event"] and t["event"] not in seen:
            seen.append(t["event"])
    return seen


def parse(text):
    machine = {"states": [], "initial": None, "transitions": [], "final": []}
    names = {}                                   # mermaid id -> state name

    def name_of(ident):
        return names.get(ident, ident)

    def add_state(name):
        if name not in machine["states"]:
            machine["states"].append(name)

    for raw in text.splitlines():
        line = raw.strip()
        if (not line or line.startswith("%%") or line.startswith("stateDiagram")
                or line.startswith("direction")):
            continue
        m = re.match(r'^state\s+"([^"]+)"\s+as\s+([A-Za-z_]\w*)$', line)
        if m:
            names[m.group(2)] = m.group(1)
            add_state(m.group(1))
            continue
        m = re.match(r"^(\[\*\]|[A-Za-z_]\w*)\s*-->\s*(\[\*\]|[A-Za-z_]\w*)\s*(?::\s*(.*))?$", line)
        if m:
            src, dst, text = m.groups()
            if src == "[*]":
                machine["initial"] = name_of(dst)
                add_state(name_of(dst))
            elif dst == "[*]":
                add_state(name_of(src))
                machine["final"].append(name_of(src))
            else:
                event, guard, action = parse_label(text or "")
                add_state(name_of(src))
                add_state(name_of(dst))
                machine["transitions"].append({"from": name_of(src), "event": event, "guard": guard,
                                               "action": action, "to": name_of(dst)})
            continue
        m = re.match(r"^(?:state\s+)?([A-Za-z_]\w*)$", line)
        if m:
            add_state(name_of(m.group(1)))
    return machine


def write(machine, header=()):
    out = [f"%% {line}" for line in header] + ["stateDiagram-v2", "    direction LR"]
    for s in machine["states"]:
        ident = state_id(s)
        out.append(f'    state "{s}" as {ident}' if ident != s else f"    {ident}")
    if machine["initial"]:
        out.append(f"    [*] --> {state_id(machine['initial'])}")
    for t in machine["transitions"]:
        text = label(t)
        out.append(f"    {state_id(t['from'])} --> {state_id(t['to'])}" + (f" : {text}" if text else ""))
    for s in machine["final"]:
        out.append(f"    {state_id(s)} --> [*]")
    return "\n".join(out) + "\n"
