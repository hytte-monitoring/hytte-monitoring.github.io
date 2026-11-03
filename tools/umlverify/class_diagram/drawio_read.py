"""class.drawio -> class model.

Recognises the shapes of draw.io's UML class palette:

    class       a swimlane; a «interface» / «enumeration» / «abstract» line sets the
                kind, and an italic name also means abstract
    members     the swimlane's child text rows, one member per line:
                `+ name: Type` and `+ method(a: Type): Return`; an underlined row is
                static, an italic method abstract
    divider     a `line` row; bare words above it are enum values
    relations   styled edges between classes (or their rows), with cardinality
                labels at either end

Anything it cannot read becomes a warning, never a silent drop: a dropped element
would look exactly like an implementation mistake.
"""
import re

from ..core.drawio import Page, font, geometry, lines, routing_style, waypoints
from .elements import relation_key
from .mermaid import REVERSED, split_params

MULTIPLICITY = re.compile(r"^(\d+|\*|n|\d+\s*\.\.\s*(\d+|\*|n))$")


def _mermaid_type(t):
    return t.strip().replace("<", "~").replace(">", "~")


def _relation(style):
    """Edge style -> (mermaid arrow, owning end) or None. Owning end: 'source' or 'target'."""
    st = style or ""
    dashed = "dashed=1" in st
    start = re.search(r"startArrow=(\w+)", st)
    end = re.search(r"endArrow=(\w+)", st)
    start, end = (start.group(1) if start else "none"), (end.group(1) if end else "classic")
    filled = lambda which: f"{which}Fill=0" not in st
    if start.startswith("diamond"):
        return ("*--" if filled("start") else "o--"), "source"
    if end.startswith("diamond"):
        return ("*--" if filled("end") else "o--"), "target"
    if end == "block" and not filled("end"):
        return ("<|.." if dashed else "<|--"), "target"
    if start == "block" and not filled("start"):
        return ("<|.." if dashed else "<|--"), "source"
    if end in ("open", "classic", "none", "openThin"):
        return ("..>" if dashed else "-->"), "source"
    return None


def read(path):
    """-> (types, relations, layout, warnings), from the first page.

    types and relations are the model mermaid.py reads and writes. layout is how
    the design was drawn, so comparisons keep the same arrangement:
    {"classes": {name: (x, y, width, height)}, "edges": {relation key: {"style", "points"}}}.
    """
    page = Page(path)
    types, layout, owner, warnings = {}, {}, {}, []

    for cid, value, c in page.cells:
        style = c.get("style") or ""
        if c.get("vertex") != "1" or "swimlane" not in style:
            continue
        stereo, title = None, ""
        for line in lines(value):
            m = re.match(r"^(?:«|<<)\s*(\w+)\s*(?:»|>>)$", line)
            if m:
                stereo = m.group(1).lower()
            else:
                title = line
        m = re.match(r"^([A-Za-z_]\w*)\s*(?:<\s*(\w+)\s*>)?$", title)
        if not m:
            warnings.append(f"shape {title!r} looks like a class but its name is not readable; skipped")
            continue
        name, generic = m.groups()
        kind = stereo if stereo in ("interface", "enumeration", "abstract") else (
            "abstract" if font(style) & 2 else "class")
        t = {"name": name, "generic": generic, "kind": kind,
             "attrs": [], "methods": [], "literals": []}
        types[name] = t
        owner[cid] = name
        g = geometry(c)
        layout[name] = (g.get("x", 0), g.get("y", 0), g.get("width", 240), g.get("height", 0))

        divided = False
        rows = sorted(page.children(cid), key=lambda r: geometry(r[2]).get("y", 0))
        for rid, rvalue, rc in rows:
            owner[rid] = name                      # edges may attach to a row
            rstyle = rc.get("style") or ""
            if rstyle.startswith("line;"):
                divided = True
                continue
            bits = font(rstyle)
            for line in lines(rvalue):
                mm = re.match(r"^([+\-#~])\s*(\w+)\s*\((.*)\)\s*(?::\s*(.+))?$", line)
                if mm:
                    vis, mname, args, ret = mm.groups()
                    params = []
                    for p in split_params(args):
                        pn, _, pt = p.partition(":")
                        params.append(f"{_mermaid_type(pt)} {pn.strip()}" if pt else _mermaid_type(pn))
                    t["methods"].append({"vis": vis, "name": mname, "args": ", ".join(params),
                                         "ret": _mermaid_type(ret or "void"),
                                         "static": bool(bits & 4),
                                         "abstract": bool(bits & 2) and not bits & 4})
                    continue
                mm = re.match(r"^([+\-#~])\s*(\w+)\s*:\s*(.+)$", line)
                if mm:
                    vis, aname, atype = mm.groups()
                    t["attrs"].append({"vis": vis, "name": aname, "type": _mermaid_type(atype),
                                       "static": bool(bits & 4)})
                    continue
                if not divided and re.match(r"^\w+$", line):
                    t["literals"].append(line)
                    continue
                warnings.append(f"{name}: could not read member {line!r}; skipped")

    relations, edges = [], {}
    for cid, value, c in page.cells:
        if c.get("edge") != "1":
            continue
        src, dst = owner.get(c.get("source")), owner.get(c.get("target"))
        if not src or not dst:
            warnings.append(f"a connector labelled {value!r} is not attached to two classes; skipped")
            continue
        found = _relation(c.get("style"))
        if found is None:
            warnings.append(f"connector {src} -> {dst}: unrecognised arrow style; skipped")
            continue
        arrow, owning_end = found
        # Labels at an end are its multiplicity and its role name (the member's name).
        cards = {"source": None, "target": None}
        roles = {"source": None, "target": None}
        for _, lvalue, lc in page.children(cid):
            x = geometry(lc).get("x", 0)
            text = " ".join(lines(lvalue))
            if x and text:
                end = "source" if x < 0 else "target"
                if MULTIPLICITY.match(text):
                    cards[end] = text.replace(" ", "")
                else:
                    roles[end] = text
        # mermaid writes the owning end first; for inheritance that is the parent
        # (`Base <|-- Derived`), which _relation reports as the owning end.
        first, second = ("source", "target") if owning_end == "source" else ("target", "source")
        ends = {"source": src, "target": dst}
        label = roles[second] or " ".join(lines(value)) or None
        relations.append({"left": ends[first], "lcard": cards[first], "arrow": arrow,
                          "rcard": cards[second], "right": ends[second], "label": label})

        # Keep the routing, oriented the way the writer draws this relation.
        drawn_from = ends[second] if arrow in REVERSED else ends[first]
        reverse = drawn_from != src
        other = ends[first] if arrow in REVERSED else ends[second]
        edges[relation_key(drawn_from, other, label)] = {"style": routing_style(c.get("style"), reverse),
                                                         "points": waypoints(c, reverse)}
    return types, relations, {"classes": layout, "edges": edges}, warnings
