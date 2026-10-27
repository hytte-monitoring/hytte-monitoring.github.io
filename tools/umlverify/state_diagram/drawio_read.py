"""state-<class>.drawio -> state machine.

Recognises the shapes of draw.io's UML palette:

    state        a rounded rectangle (`rounded=1`, or `shape=umlState`) labelled with the name
    initial      the start symbol (`shape=startState`, or a filled ellipse without a label)
    final        the end symbol (`shape=endState`); an unlabelled edge into it documents a
                 terminal state and is kept as a drawing, not counted
    transition   an edge from one state to another, labelled `event [guard] / action`

Composite states, entry/exit actions, history and choice pseudo-states are not
supported. Anything unreadable becomes a warning, never a silent drop: a dropped
element would look exactly like an implementation mistake.
"""
from ..core.drawio import (Page, geometry, label_position, lines, routing_style, style_value,
                           waypoints)
from .elements import transition_counts, transition_key
from .mermaid import parse_label


def _kind(style, text):
    st = style or ""
    if "edgeLabel" in st or st.startswith("text;") or "shape=note" in st:
        return "other"
    if "shape=startState" in st:
        return "initial"
    if "shape=endState" in st:
        return "final"
    if "ellipse" in st:
        black = (style_value(st, "fillColor") or "").lower() in ("#000000", "black", "strokecolor")
        return "initial" if black and not text else "other"
    if "swimlane" in st:
        return "composite"
    if "shape=umlState" in st or "rounded=1" in st:
        return "state" if text else "unlabelled"
    return "other"


def _box(c):
    g = geometry(c)
    return (g.get("x", 0), g.get("y", 0), g.get("width", 0), g.get("height", 0))


def read(path):
    """-> (machine, layout, warnings), from the first page.

    machine is the model mermaid.py reads and writes. layout is how the design was
    drawn, so comparisons keep the same arrangement:
        {"states": {name: (x, y, w, h)}, "initial": (x, y, w, h) or None,
         "initial_edge": {"style", "points", "label", "to"} or None,
         "finals": [{"state", "box", "style", "points"}],
         "edges": {transition key: {"style", "points", "label", "to"}}}
    """
    page = Page(path)
    machine = {"states": [], "initial": None, "transitions": [], "final": []}
    layout = {"states": {}, "initial": None, "initial_edge": None, "finals": [], "edges": {}}
    warnings, nodes, final_boxes = [], {}, {}

    edges = [(cid, value, c) for cid, value, c in page.cells if c.get("edge") == "1"]
    attached = {c.get("source") for _, _, c in edges} | {c.get("target") for _, _, c in edges}

    for cid, value, c in page.cells:
        if c.get("vertex") != "1":
            continue
        text = lines(value)
        kind = _kind(c.get("style"), text)
        if kind == "state":
            name = text[0]
            if len(text) > 1:
                warnings.append(f"state {name!r}: the lines {text[1:]} were ignored "
                                "(entry/exit actions are not supported)")
            if name in machine["states"]:
                warnings.append(f"state {name!r} is drawn twice; the second one was skipped")
                continue
            machine["states"].append(name)
            layout["states"][name] = _box(c)
            nodes[cid] = ("state", name)
        elif kind == "initial":
            nodes[cid] = ("initial", None)
            if layout["initial"] is None:
                layout["initial"] = _box(c)
        elif kind == "final":
            nodes[cid] = ("final", None)
            final_boxes[cid] = _box(c)
        elif kind == "composite":
            warnings.append(f"{(text[0] if text else 'a swimlane')!r} looks like a composite state "
                            "or a class; composite states are not supported; skipped")
        elif kind == "unlabelled":
            warnings.append("a state shape without a name was skipped")
        elif cid in attached and text:
            warnings.append(f"shape {text[0]!r} is connected by a transition but is not a state "
                            "shape (a rounded rectangle); skipped")

    drawn = []
    for cid, value, c in edges:
        text = " ".join(lines(value)) or " ".join(" ".join(lines(v)) for _, v, _ in page.children(cid))
        src, dst = nodes.get(c.get("source")), nodes.get(c.get("target"))
        entry = {"style": routing_style(c.get("style")), "points": waypoints(c),
                 "label": label_position(c)}
        if src is None or dst is None:
            warnings.append(f"the transition {text!r} is not attached to a state at both ends; skipped")
            continue
        if src[0] == "initial":
            if dst[0] != "state":
                warnings.append("the initial transition does not end at a state; skipped")
            elif machine["initial"] is not None:
                warnings.append(f"more than one initial transition; the one to {dst[1]!r} was skipped")
            else:
                machine["initial"] = dst[1]
                layout["initial_edge"] = {**entry, "to": dst[1]}
            continue
        if dst[0] == "final":
            if src[0] != "state":
                warnings.append("a transition to the end symbol does not start at a state; skipped")
            elif text.strip():
                warnings.append(f"the transition {text!r} from {src[1]!r} to the end symbol has no "
                                "C++ counterpart (a terminal state is one without outgoing "
                                "transitions); skipped")
            else:
                machine["final"].append(src[1])
                layout["finals"].append({"state": src[1], "box": final_boxes[c.get("target")],
                                         "style": entry["style"], "points": entry["points"]})
            continue
        if src[0] != "state" or dst[0] != "state":
            warnings.append(f"the transition {text!r} between {src[1] or src[0]!r} and "
                            f"{dst[1] or dst[0]!r} was skipped")
            continue
        event, guard, action = parse_label(text)
        if not event:
            warnings.append(f"the transition {src[1]} -> {dst[1]} ({text!r}) has no event; "
                            "every transition needs one")
        t = {"from": src[1], "event": event, "guard": guard, "action": action, "to": dst[1]}
        machine["transitions"].append(t)
        drawn.append((t, {**entry, "to": dst[1]}))

    counts = transition_counts(machine)
    for t, entry in drawn:
        key = transition_key(counts, t)
        if key in layout["edges"]:
            warnings.append(f"the transition {t['from']} -> {t['to']} on {t['event']!r} is drawn twice")
        layout["edges"][key] = entry
    return machine, layout, warnings
