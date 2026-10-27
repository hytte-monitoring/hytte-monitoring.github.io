"""Read and write the mermaid `sequenceDiagram` subset used by the sequence-diagram flow.

A scenario is:

    {"lifelines": [{"name", "kind"}, ...]     kind "actor" or "object"; in drawing order
     "messages":  [{"from", "to", "name", "text", "kind"}, ...]}
                                              in order; kind "call" or "return"; name is the
                                              method, text the label as drawn (`lend(b1, m1)`)

Lifelines are named by class (`order: Order` in a drawing is the lifeline `Order`); an actor
keeps its name. The initiator is the actor, or the first lifeline when there is no actor: its
messages are the ones the scenario code makes from outside every class. Return messages are
documentation: written and drawn, never compared.
"""
import re


def ident(name):
    """A mermaid identifier for a lifeline name: 'Front desk' -> 'FrontDesk'."""
    words = re.findall(r"[A-Za-z0-9_]+", name or "")
    out = "".join(w if n == 0 else w[:1].upper() + w[1:] for n, w in enumerate(words))
    return out or "L"


def message_name(text):
    """A label -> the method it names: 'lend(b1, m1)' -> 'lend', 'true' -> 'true'."""
    return re.split(r"[(:]", (text or "").strip(), maxsplit=1)[0].strip()


def initiator(scenario):
    """The lifeline whose messages come from outside the classes: the actor, else the first."""
    for l in scenario["lifelines"]:
        if l["kind"] == "actor":
            return l["name"]
    return scenario["lifelines"][0]["name"] if scenario["lifelines"] else None


def parse(text):
    scenario = {"lifelines": [], "messages": []}
    names = {}

    def name_of(i):
        return names.get(i, i)

    def add_lifeline(name, kind="object"):
        if all(l["name"] != name for l in scenario["lifelines"]):
            scenario["lifelines"].append({"name": name, "kind": kind})

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%") or line.startswith("sequenceDiagram"):
            continue
        m = re.match(r"^(actor|participant)\s+([A-Za-z_]\w*)(?:\s+as\s+(.+))?$", line)
        if m:
            kind, i, display = m.groups()
            names[i] = (display or i).strip()
            add_lifeline(names[i], "actor" if kind == "actor" else "object")
            continue
        m = re.match(r"^([A-Za-z_]\w*)\s*(-->>|->>|-->|->|-x|--x|-\)|--\))\s*([A-Za-z_]\w*)\s*:\s*(.*)$", line)
        if m:
            src, arrow, dst, label = m.groups()
            add_lifeline(name_of(src))
            add_lifeline(name_of(dst))
            scenario["messages"].append({"from": name_of(src), "to": name_of(dst),
                                         "name": message_name(label), "text": label.strip(),
                                         "kind": "return" if arrow.startswith("--") else "call"})
    return scenario


def write(scenario, header=()):
    out = [f"%% {line}" for line in header] + ["sequenceDiagram"]
    for l in scenario["lifelines"]:
        i = ident(l["name"])
        out.append(f"    {'actor' if l['kind'] == 'actor' else 'participant'} {i}"
                   + (f" as {l['name']}" if i != l["name"] else ""))
    for m in scenario["messages"]:
        arrow = "-->>" if m["kind"] == "return" else "->>"
        out.append(f"    {ident(m['from'])}{arrow}{ident(m['to'])}: {m['text']}")
    return "\n".join(out) + "\n"
