"""sequence-<scenario>.drawio -> scenario.

Recognises the shapes of draw.io's UML palettes:

    lifeline     `shape=umlLifeline`, whatever its participant style. Its label names it:
                 `order: Order`, `:Order` and `Order` are all the lifeline `Order`; an actor
                 lifeline (`participant=umlActor`), or a standalone `shape=umlActor`, keeps its
                 label as its name
    activation   a bar with `perimeter=orthogonalPerimeter`, inside a lifeline or placed over
                 one; messages may attach to it instead of the lifeline
    message      an edge between two lifelines, directly or through their activations; dashed
                 is a return, anything else a call; the label is the method, `lend(b1, m1)`
    fragment     `shape=umlFrame` (alt, loop, opt): not supported, a warning; the messages
                 inside are read in order like the others

An edge attached to nothing is placed on the lifelines nearest to its end points. Messages
are ordered by their height on the page, which draw.io keeps in a waypoint, an entry or exit
point, or an end point, depending on how the message was drawn. Creation messages
(`«create»`, `new`) and unlabelled calls are warnings: constructors are never messages.
"""
import re

from ..core.drawio import Page, geometry, lines, style_value, waypoints
from .mermaid import message_name

CREATE = re.compile(r"^\s*(«\s*create\s*»|<<\s*create\s*>>|new\b)", re.I)


def _name(text, actor):
    label = text[0] if text else ""
    if actor:
        return label or "Actor"
    name, colon, cls = label.rpartition(":")
    return (cls.strip() or name.strip()) if colon else label


def _terminal_point(cell, which):
    g = cell.find("mxGeometry")
    if g is None:
        return None
    p = next((p for p in g.findall("mxPoint") if p.get("as") == which), None)
    return (float(p.get("x", 0)), float(p.get("y", 0))) if p is not None else None


def read(path):
    """-> (scenario, layout, warnings), from the first page.

    layout: {"lifelines": {name: (x, y, w, h)}, "messages": {index: y}} — where the person
    put things, so the comparison keeps the arrangement.
    """
    page = Page(path)
    warnings = []
    lifelines, activations, frames = {}, {}, []

    for cid, value, c in page.cells:
        if c.get("vertex") != "1":
            continue
        st = c.get("style") or ""
        g = geometry(c)
        box = (g.get("x", 0), g.get("y", 0), g.get("width", 0), g.get("height", 0))
        if "shape=umlLifeline" in st or "shape=umlActor" in st:
            actor = "umlActor" in st
            name = _name(lines(value), actor)
            if not name:
                warnings.append("a lifeline without a name was skipped")
                continue
            if any(l["name"] == name for l in lifelines.values()):
                warnings.append(f"two lifelines are named {name!r}; only one object per class "
                                "can be told apart, so the second was skipped")
                continue
            lifelines[cid] = {"name": name, "kind": "actor" if actor else "object", "box": box,
                              "head": float(style_value(st, "size") or 40)}
        elif "shape=umlFrame" in st:
            frames.append((lines(value) or ["fragment"])[0])

    for cid, value, c in page.cells:           # activations, once every lifeline is known
        st = c.get("style") or ""
        if c.get("vertex") != "1" or "perimeter=orthogonalPerimeter" not in st:
            continue
        g = geometry(c)
        parent = c.get("parent")
        if parent in lifelines:
            lx, ly = lifelines[parent]["box"][:2]
            activations[cid] = (parent, ly + g.get("y", 0), g.get("height", 0))
        else:
            cx = g.get("x", 0) + g.get("width", 0) / 2
            over = next((lid for lid, l in lifelines.items()
                         if l["box"][0] <= cx <= l["box"][0] + l["box"][2]), None)
            if over:
                activations[cid] = (over, g.get("y", 0), g.get("height", 0))

    for label in frames:
        warnings.append(f"the fragment {label!r} is not supported (alt, loop and opt cannot be "
                        "verified from one run); the messages inside it were read in order")

    def owner(cell_id):
        if cell_id in lifelines:
            return cell_id
        if cell_id in activations:
            return activations[cell_id][0]
        return None

    def nearest(point):
        if point is None:
            return None
        best = min(lifelines.items(), default=(None, None),
                   key=lambda item: abs(item[1]["box"][0] + item[1]["box"][2] / 2 - point[0]))
        lid, l = best
        return lid if l and abs(l["box"][0] + l["box"][2] / 2 - point[0]) <= max(40, l["box"][2]) else None

    def end_y(cell, end, cell_id):
        """Where an end of an edge sits vertically, from its exit/entry constraint."""
        fy = style_value(cell.get("style"), f"{end}Y")
        if fy is None:
            return None
        if cell_id in lifelines:
            _, ly, _, lh = lifelines[cell_id]["box"]
            return ly + float(fy) * lh
        if cell_id in activations:
            _, ay, ah = activations[cell_id]
            return ay + float(fy) * ah
        return None

    found = []
    for n, (cid, value, c) in enumerate(page.cells):
        if c.get("edge") != "1":
            continue
        st = c.get("style") or ""
        text = " ".join(lines(value)) or " ".join(" ".join(lines(v)) for _, v, _ in page.children(cid))
        src_cell, dst_cell = c.get("source"), c.get("target")
        pts = waypoints(c)
        sp, tp = _terminal_point(c, "sourcePoint"), _terminal_point(c, "targetPoint")
        src = owner(src_cell) or nearest(sp or (pts[0] if pts else None))
        dst = owner(dst_cell) or nearest(tp or (pts[-1] if pts else None))
        if src is None or dst is None:
            if lifelines and (text or src or dst):
                warnings.append(f"the message {text!r} is not attached to a lifeline at both ends; skipped")
            continue
        kind = "return" if "dashed=1" in st else "call"
        if kind == "call" and CREATE.match(text):
            warnings.append(f"the creation message {text!r} to {lifelines[dst]['name']} is not "
                            "compared (constructors are never messages); skipped")
            continue
        if kind == "call" and not message_name(text):
            warnings.append(f"a message from {lifelines[src]['name']} to {lifelines[dst]['name']} "
                            "has no label saying which method it calls; skipped")
            continue
        ys = ([pts[0][1]] if pts else []) + [end_y(c, "exit", src_cell), end_y(c, "entry", dst_cell),
                                           sp[1] if sp else None, tp[1] if tp else None]
        y = next((v for v in ys if v is not None), None)
        if y is None:
            for cell_id in (dst_cell, src_cell):
                if cell_id in activations:
                    y = activations[cell_id][1]
                    break
        if y is None:
            box = lifelines[src]["box"]
            y = box[1] + box[3] / 2
        found.append((y, n, {"from": lifelines[src]["name"], "to": lifelines[dst]["name"],
                             "name": message_name(text), "text": text.strip(), "kind": kind}))

    ordered = sorted(lifelines.values(), key=lambda l: l["box"][0])
    scenario = {"lifelines": [{"name": l["name"], "kind": l["kind"]} for l in ordered],
                "messages": [m for _, _, m in sorted(found, key=lambda t: (t[0], t[1]))]}
    layout = {"lifelines": {l["name"]: l["box"] for l in ordered},
              "messages": {i: y for i, (y, _, _) in enumerate(sorted(found, key=lambda t: (t[0], t[1])))}}
    return scenario, layout, warnings
