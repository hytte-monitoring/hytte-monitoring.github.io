"""state machine -> draw.io shapes, and the colour-coded comparison.

Writes the shapes drawio_read.py recognises (rounded-rectangle states, the start and
end symbols, labelled edges), so everything this flow writes it can also read back.

The comparison has two pages, like a class comparison:

    1 - Design (human)       changed elements amber, missing elements red
    2 - Implemented (AI)     changed elements amber, extra elements green

States keep their positions from the design, and every transition the person drew
keeps its routing and label position; states the design lacks go in a column on the
right, under the legend, and transitions nobody drew are routed around the others.
Events have no shape of their own: they show on the transitions that use them.
"""
import html

from ..core.compare import nname
from ..core.drawio import cell, legend, merge_styles, mxfile, paint, status_marks
from ..core.routing import route, segment_clear
from .elements import INITIAL, transition_counts, transition_key
from .mermaid import label, parse

STATE = "rounded=1;whiteSpace=wrap;html=1;"
START = "ellipse;html=1;shape=startState;fillColor=#000000;strokeColor=#000000;"
END = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
EDGE = "html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;endArrow=open;endSize=12;"
STATE_W, STATE_H, DOT = 120, 60, 30


def _width(name):
    return max(STATE_W, int(len(name) * 7.5) + 30)


def _beside(box, side="left"):
    """A 30 px symbol beside a box, level with its middle."""
    x, y, w, h = box
    return ((x - 70 if side == "left" else x + w + 40), y + h / 2 - DOT / 2, DOT, DOT)


# Where the label of the k-th line in a corridor sits along its line (0 = the middle,
# -0.5 = a quarter of the way from the source), so that labels of parallel lines,
# which are only a few pixels apart, do not land on top of each other.
LABEL_ALONG = (0, -0.5, 0.5, -0.25, 0.25)


class _Ports:
    """Attachment points for lines nobody drew, spread so lines sharing a side do not overlap."""

    def __init__(self):
        self.used = {}

    def _next(self, name, side):
        n = self.used.get((name, side), 0)
        self.used[(name, side)] = n + 1
        return n

    def attach(self, src, dst, sbox, dbox, others):
        """-> (routing style, waypoints, label position): a straight line when one is
        clear of other boxes, otherwise a route around them."""
        sx, sy, sw, sh = sbox
        dx, dy, dw, dh = dbox
        overlap_y = min(sy + sh, dy + dh) - max(sy, dy)
        overlap_x = min(sx + sw, dx + dw) - max(sx, dx)
        if overlap_y > 20:                        # side by side: a horizontal line
            right = dx >= sx + sw
            k = max(self._next(src, "right" if right else "left"),
                    self._next(dst, "left" if right else "right"))
            y = (max(sy, dy) + min(sy + sh, dy + dh)) / 2 + 18 * ((k + 1) // 2) * (1 if k % 2 else -1)
            y = min(max(y, max(sy, dy) + 8), min(sy + sh, dy + dh) - 8)
            a, b = ((sx + sw) if right else sx, y), (dx if right else (dx + dw), y)
            if segment_clear(a, b, others):
                return (f"exitX={1 if right else 0};exitY={(y - sy) / sh:.4f};"
                        f"entryX={0 if right else 1};entryY={(y - dy) / dh:.4f};", [], _along(k))
        elif overlap_x > 20:                      # stacked: a vertical line
            below = dy >= sy + sh
            k = max(self._next(src, "bottom" if below else "top"),
                    self._next(dst, "top" if below else "bottom"))
            x = (max(sx, dx) + min(sx + sw, dx + dw)) / 2 + 24 * ((k + 1) // 2) * (1 if k % 2 else -1)
            x = min(max(x, max(sx, dx) + 8), min(sx + sw, dx + dw) - 8)
            a, b = (x, (sy + sh) if below else sy), (x, dy if below else (dy + dh))
            if segment_clear(a, b, others):
                return (f"exitX={(x - sx) / sw:.4f};exitY={1 if below else 0};"
                        f"entryX={(x - dx) / dw:.4f};entryY={0 if below else 1};", [], _along(k))
        found = route(sbox, dbox, others + [sbox, dbox])
        if found:
            (ex, ey), (nx, ny), points = found
            return f"exitX={ex};exitY={ey};entryX={nx};entryY={ny};", points, None
        return "", [], None


def _along(k):
    at = LABEL_ALONG[k % len(LABEL_ALONG)]
    return (at, 0, 0, 0) if at else None


def _loop(box):
    """A self-transition: out of the top, round the top-right corner, back into the right side."""
    x, y, w, h = box
    return ("exitX=0.75;exitY=0;entryX=1;entryY=0.25;",
            [(x + 0.75 * w, y - 30), (x + w + 30, y - 30), (x + w + 30, y + 0.25 * h)], None)


def _box_xml(x, y, w, h):
    return f'          <mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" as="geometry" />\n'


def _edge_xml(points, label_pos):
    lx, ly, ox, oy = label_pos or (0, 0, 0, 0)
    attrs = 'relative="1"' + (f' x="{lx:g}"' if lx else "") + (f' y="{ly:g}"' if ly else "")
    out = f'          <mxGeometry {attrs} as="geometry">\n'
    if points:
        out += ('            <Array as="points">\n'
                + "".join(f'              <mxPoint x="{px:g}" y="{py:g}" />\n' for px, py in points)
                + '            </Array>\n')
    if ox or oy:
        out += f'            <mxPoint x="{ox:g}" y="{oy:g}" as="offset" />\n'
    return out + '          </mxGeometry>\n'


def build_cells(machine, layout, prefix="", mark=None):
    """State machine -> draw.io cells. layout: see drawio_read.read (every state placed).

    mark(category, **info) may return (status, tooltip) to colour an element:
    mark("state", name=...), mark("transition", key=...), mark("initial").
    """
    mark = mark or (lambda category, **info: None)
    cells, ids = [], {}
    nid = [1]

    def new_id(kind="s"):
        nid[0] += 1
        return f"{prefix}{kind}{nid[0]}"

    boxes = {name: layout["states"][name] for name in machine["states"]}
    by_norm = {nname(name): name for name in machine["states"]}
    initial = machine["initial"] if machine["initial"] in boxes else None
    dot = (layout.get("initial") or _beside(boxes[initial])) if initial else None
    finals = layout.get("finals")
    if finals is None:                            # a fresh drawing: place the end symbols
        finals = [{"state": s, "box": _beside(boxes[s], "right"), "style": None, "points": []}
                  for s in machine["final"] if s in boxes]
    finals = [{**f, "state": by_norm.get(nname(f["state"]))} for f in finals]
    obstacles = list(boxes.values()) + ([dot] if dot else []) + [f["box"] for f in finals]
    ports = _Ports()

    def fresh(src, dst, sbox, dbox):
        """-> (routing style, waypoints, label position) for a line nobody drew."""
        if src == dst:
            return _loop(sbox)
        return ports.attach(src, dst, sbox, dbox, [b for b in obstacles if b not in (sbox, dbox)])

    def edge(src_id, dst_id, text, style, points, label_pos, status, tip):
        cells.append(cell(new_id("e"), html.escape(text), paint(merge_styles(EDGE, style), status, "edge"),
                          f"{prefix}1", _edge_xml(points, label_pos), kind="edge",
                          extra=f' source="{src_id}" target="{dst_id}"', tooltip=tip))

    for name in machine["states"]:
        sid = new_id()
        ids[name] = sid
        status, tip = mark("state", name=name) or (None, None)
        cells.append(cell(sid, html.escape(name), paint(STATE, status, "shape"), f"{prefix}1",
                          _box_xml(*boxes[name]), tooltip=tip))

    if initial:
        did = new_id("i")
        cells.append(cell(did, "", START, f"{prefix}1", _box_xml(*dot)))
        status, tip = mark("initial") or (None, None)
        kept = layout.get("initial_edge")
        if kept and nname(kept["to"]) == nname(initial):
            style, points, label_pos = kept["style"], kept["points"], kept["label"]
        else:
            style, points, label_pos = fresh(INITIAL, initial, dot, boxes[initial])
        edge(did, ids[initial], "", style, points, label_pos, status, tip)

    counts = transition_counts(machine)
    for t in machine["transitions"]:
        key = transition_key(counts, t)
        status, tip = mark("transition", key=key) or (None, None)
        kept = layout.get("edges", {}).get(key)
        if kept and nname(kept["to"]) == nname(t["to"]):
            style, points, label_pos = kept["style"], kept["points"], kept["label"]
        else:
            style, points, label_pos = fresh(t["from"], t["to"], boxes[t["from"]], boxes[t["to"]])
        edge(ids[t["from"]], ids[t["to"]], label(t), style, points, label_pos, status, tip)

    for f in finals:                              # documentation: terminal states, drawn plain
        if f["state"] not in ids:
            continue
        fid = new_id("f")
        cells.append(cell(fid, "", END, f"{prefix}1", _box_xml(*f["box"])))
        if f["style"] is None:
            style, points, _ = fresh(f["state"], "[end]", boxes[f["state"]], f["box"])
        else:
            style, points = f["style"], f["points"]
        edge(ids[f["state"]], fid, "", style, points, None, None, None)
    return cells


def place(machine, layout):
    """The design's layout, plus positions for states it does not have.

    Returns (layout, spare_x). States the design lacks are stacked in a column right
    of the design, which also holds the legend on comparison pages.
    """
    drawn = {nname(name): box for name, box in layout.get("states", {}).items()}
    boxes = (list(drawn.values()) + ([layout["initial"]] if layout.get("initial") else [])
             + [f["box"] for f in layout.get("finals") or []])
    right = max((b[0] + b[2] for b in boxes), default=0)
    spare_x, y = right + 80, 260
    states = {}
    for name in machine["states"]:                # a state is looked up the way names compare
        box = drawn.get(nname(name))
        if box is None:
            box = (spare_x, y, _width(name), STATE_H)
            y += STATE_H + 60
        states[name] = box
    return {**layout, "states": states}, spare_x


def document(machine, layout, name="State machine"):
    """A plain one-page .drawio of a state machine — e.g. to start a new design.

    layout may give positions for some states ({"states": {name: (x, y, w, h)}}) and
    the start symbol ("initial"); everything else is placed and routed here.
    """
    placed, _ = place(machine, {"states": {}, "initial": None, "initial_edge": None,
                                "finals": None, "edges": {}, **layout})
    return mxfile([(name, "page", build_cells(machine, placed, prefix="page-"))])


# --------------------------------------------------------------------- comparison

def _marker(table):
    def mark(category, **info):
        if category == "state":
            key = nname(info["name"])
        elif category == "initial":
            key = INITIAL
            category = "transition"
        else:
            key = info["key"]
        return table.get((category, key))
    return mark


def comparison(design_mmd, implemented_mmd, layout, result, design_label, implemented_label):
    """Both machines as a two-page .drawio document, colour-coded from `result`."""
    marks = status_marks(result)
    pages = [
        ("1 - Design (human)", design_mmd, "design", "DESIGN", design_label,
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("missing", f"Missing from the implementation ({len(result.missing)})")]),
        ("2 - Implemented (AI)", implemented_mmd, "implemented", "IMPLEMENTED STATE MACHINE",
         implemented_label,
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("extra", f"Extra, not in the design ({len(result.extra)})")]),
    ]
    out = []
    for name, path, pid, title, subtitle, key in pages:
        machine = parse(path.read_text())
        positions, spare_x = place(machine, layout)
        cells = build_cells(machine, positions, prefix=f"{pid}-", mark=_marker(marks[pid]))
        cells += legend(f"{pid}-", title, subtitle, key, x=spare_x)
        out.append((name, pid, cells))
    return mxfile(out)
