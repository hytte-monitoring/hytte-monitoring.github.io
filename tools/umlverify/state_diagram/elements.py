"""State machine -> elements for core.compare.

    category     identified by                          details compared
    state        name                                   (none: a state is there or not)
    event        name                                   (none)
    transition   source state + event                   target state, guard, action
                 + guard, when that state has several   target state, action
                   transitions on the same event
    the initial transition `[*] --> S`, one per machine  the state it enters

The guard joins a transition's identity only when it has to: a state with `pay [inStock]`
and `pay [outOfStock]` has two transitions on `pay`. Otherwise the guard is a detail, so a
forgotten guard is one *changed* transition, not one missing plus one extra.
"""
from collections import Counter

from ..core.compare import Element, nname
from .mermaid import events, label, parse

COLUMNS = [("state", "States"), ("event", "Events"), ("transition", "Transitions")]
INITIAL = "[*]"


def transition_counts(machine):
    """How many transitions each (state, event) pair has; see transition_key."""
    return Counter((nname(t["from"]), nname(t["event"])) for t in machine["transitions"])


def transition_key(counts, t):
    base = (nname(t["from"]), nname(t["event"]))
    return base if counts[base] <= 1 else base + (nname(t["guard"]),)


def elements(mermaid_text):
    """-> ({(category, key): Element}, machine)"""
    machine = parse(mermaid_text)
    found = {}

    def add(e):
        found[(e.category, e.key)] = e

    for s in machine["states"]:
        add(Element("state", nname(s), s, s, {}))
    for ev in events(machine):
        add(Element("event", nname(ev), ev, ev, {}))
    if machine["initial"]:
        add(Element("transition", INITIAL, "[*] -->", f"[*] --> {machine['initial']}",
                    {"initial state": (nname(machine["initial"]), machine["initial"])}))
    counts = transition_counts(machine)
    for t in machine["transitions"]:
        key = transition_key(counts, t)
        details = {"target state": (nname(t["to"]), t["to"])}
        if len(key) == 2:
            details["guard"] = (nname(t["guard"]), t["guard"] or "none")
        details["action"] = (nname(t["action"]), t["action"] or "none")
        name = f"{t['from']} on {t['event'] or '(no event)'}" + (f" [{t['guard']}]" if len(key) == 3 else "")
        text = label(t)
        add(Element("transition", key, name,
                    f"{t['from']} --> {t['to']}" + (f" : {text}" if text else ""), details))
    return found, machine
