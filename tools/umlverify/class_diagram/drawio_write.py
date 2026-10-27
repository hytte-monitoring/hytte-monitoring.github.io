"""class model -> draw.io shapes, and the colour-coded comparison.

Writes the same shapes drawio_read.py recognises (swimlane classes, member rows,
styled edges), so everything this flow writes it can also read back.

The comparison has two pages:

    1 - Design (human)       changed elements amber, missing elements red
    2 - Implemented (AI)     changed elements amber, extra elements green,
                             dependencies that are not counted grey

Colours come from the same comparison result as the report, so every coloured
element is a row in the report and vice versa. Classes keep their positions from
class.drawio; classes the design lacks go in a column on the right, under the legend.
"""
import html

from ..core.compare import nname
from ..core.drawio import cell, legend, merge_styles, mxfile, paint, status_marks, style_value
from ..core.routing import route, segment_clear
from .elements import relation_key
from .mermaid import REVERSED, parse, split_params

SWIMLANE = ("swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;"
            "horizontal=1;horizontalStack=0;resizeParent=1;resizeParentMax=0;"
            "html=1;whiteSpace=wrap;")
ROW = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;"
       "spacingRight=4;overflow=hidden;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
       "rotatable=0;whiteSpace=wrap;html=1;")
DIVIDER = ("line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;"
           "spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];"
           "portConstraint=eastwest;")
END_LABEL = "edgeLabel;resizable=0;html=1;"

# One style per relation; drawio_read.py recognises each of these. The open
# arrowhead is navigability: the owning class can reach the other one. In C++ every
# relation is one-way (a member in the owner), so every relation has one.
EDGE_BASE = "html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;"
EDGE_STYLE = {
    "<|--": "endArrow=block;endSize=16;endFill=0;",
    "<|..": "endArrow=block;endSize=16;endFill=0;dashed=1;",
    "*--": "startArrow=diamondThin;startFill=1;startSize=14;endArrow=open;endSize=12;",
    "o--": "startArrow=diamondThin;startFill=0;startSize=14;endArrow=open;endSize=12;",
    "-->": "endArrow=open;endSize=12;",
    "..>": "endArrow=open;endSize=12;dashed=1;",
}

TITLE_H, STEREO_H, ROW_H, DIV_H = 26, 14, 26, 8


def _uml_type(t):
    """mermaid ~T~ generics -> <T>."""
    out, depth = [], 0
    for ch in t:
        if ch == "~":
            out.append("<" if depth == 0 else ">")
            depth = 1 - depth
        else:
            out.append(ch)
    return "".join(out)


def _member(a):
    return f"{a['vis']} {a['name']}: {_uml_type(a['type'])}"


def _method(m):
    params = []
    for part in split_params(m["args"]):
        bits = part.rsplit(" ", 1)
        params.append(f"{bits[1]}: {_uml_type(bits[0])}" if len(bits) == 2 else _uml_type(part))
    return f"{m['vis']} {m['name']}({', '.join(params)}): {_uml_type(m['ret'])}"


def _text_width(text, italic=False):
    """Rough width of a line of 12px Helvetica (italic runs wider), plus the row's padding."""
    return int(len(text) * (7.6 if italic else 7.0)) + 24


def _side(box, point):
    """Which side of box (x, y, w, h) a point outside or on it is nearest to."""
    x, y, w, h = box
    px, py = point
    dx = (px - (x + w / 2)) / (w / 2 or 1)
    dy = (py - (y + h / 2)) / (h / 2 or 1)
    if abs(dx) >= abs(dy):
        return "right" if dx > 0 else "left"
    return "bottom" if dy > 0 else "top"


def _constraint_side(style, end):
    """The side an exitX/exitY (end='exit') or entryX/entryY constraint attaches to."""
    x, y = style_value(style, f"{end}X"), style_value(style, f"{end}Y")
    if x is None or y is None:
        return None
    x, y = float(x), float(y)
    if x in (0.0, 1.0):
        return "left" if x == 0 else "right"
    if y in (0.0, 1.0):
        return "top" if y == 0 else "bottom"
    return None


class _Ports:
    """Default attachment points, spread out so lines sharing a side do not overlap."""

    def __init__(self):
        self.used = {}

    def next(self, name, side):
        n = self.used.get((name, side), 0)
        self.used[(name, side)] = n + 1
        return n

    def attach(self, src, dst, sbox, dbox):
        """-> style for exit/entry points, or "" to leave routing to draw.io."""
        sx, sy, sw, sh = sbox
        dx, dy, dw, dh = dbox
        overlap_y = min(sy + sh, dy + dh) - max(sy, dy)
        overlap_x = min(sx + sw, dx + dw) - max(sx, dx)
        if overlap_y > 30:                       # side by side: connect at header height
            right = dx >= sx + sw
            s_side, d_side = ("right", "left") if right else ("left", "right")
            y = max(sy, dy) + TITLE_H / 2 + 22 * max(self.next(src, s_side), self.next(dst, d_side))
            y = min(y, min(sy + sh, dy + dh) - 6)
            return (f"exitX={1 if right else 0};exitY={(y - sy) / sh:.4f};"
                    f"entryX={0 if right else 1};entryY={(y - dy) / dh:.4f};")
        if overlap_x > 30:                       # stacked: connect bottom to top
            below = dy >= sy + sh
            s_side, d_side = ("bottom", "top") if below else ("top", "bottom")
            k = max(self.next(src, s_side), self.next(dst, d_side))
            x = max(sx, dx) + overlap_x / 2 + (60 * ((k + 1) // 2) * (1 if k % 2 else -1))
            return (f"exitX={(x - sx) / sw:.4f};exitY={1 if below else 0};"
                    f"entryX={(x - dx) / dw:.4f};entryY={0 if below else 1};")
        return ""


def _end_labels(prefix_id, eid, side, at, role, mult):
    """Role name and multiplicity beside one end of an edge, as UML draws them.

    side: the side of the class the edge meets; at: 'source' or 'target'. The role
    name goes on one side of the line and the multiplicity on the other, both just
    outside the class so they never sit on an arrowhead or diamond.
    """
    x = "1" if at == "target" else "-1"
    placement = {   # side -> (role style, role offset, mult style, mult offset)
        "left":   ("align=right;verticalAlign=bottom;", (-20, -1), "align=right;verticalAlign=top;", (-20, 1)),
        "right":  ("align=left;verticalAlign=bottom;", (20, -1), "align=left;verticalAlign=top;", (20, 1)),
        "top":    ("align=left;verticalAlign=bottom;", (4, -18), "align=right;verticalAlign=bottom;", (-4, -18)),
        "bottom": ("align=left;verticalAlign=top;", (4, 18), "align=right;verticalAlign=top;", (-4, 18)),
    }[side]
    cells = []
    for n, (text, style, (ox, oy)) in enumerate(((role, placement[0], placement[1]),
                                                  (mult, placement[2], placement[3]))):
        if text:
            cells.append(cell(f"{prefix_id}{n}", html.escape(text), END_LABEL + style, eid,
                              f'          <mxGeometry x="{x}" relative="1" as="geometry">\n'
                              f'            <mxPoint x="{ox}" y="{oy}" as="offset" />\n'
                              f'          </mxGeometry>\n',
                              extra=' connectable="0"'))
    return cells


def build_cells(types, relations, layout, prefix="", mark=None):
    """Class model -> draw.io cells.

    layout: {"classes": {name: (x, y, width)}, "edges": {relation key: {"style", "points"}}}.
    Edges found in layout["edges"] keep that routing (waypoints and attachment
    points); the others get default attachment points. mark(category, **info) may
    return (status, tooltip) to colour an element; without it everything is plain.
    """
    cells, ids, boxes = [], {}, {}
    nid = [1]
    mark = mark or (lambda category, **info: None)

    def new_id(kind="c"):
        nid[0] += 1
        return f"{prefix}{kind}{nid[0]}"

    for name, t in types.items():
        x, y, w = layout["classes"][name][:3]
        cid = new_id()
        ids[name] = cid

        plain_title = name + (f"<{t['generic']}>" if t["generic"] else "")
        stereo = {"interface": "«interface»",
                  "enumeration": "«enumeration»"}.get(t["kind"], "")
        label = f"{stereo}<br>{html.escape(plain_title)}" if stereo else html.escape(plain_title)
        head = TITLE_H + (STEREO_H if stereo else 0)

        style = SWIMLANE + f"startSize={head};" + ("fontStyle=3;" if t["kind"] == "abstract" else "")
        status, tip = mark("class", name=name) or (None, None)
        style = paint(style, status, "shape")

        rows, h, texts = [], head, [(plain_title, t["kind"] == "abstract")]

        def add_row(text, extra, marked):
            st, tp = marked or (None, None)
            # draw.io clips italic text to its upright width when overflow is hidden,
            # cutting off the last letter, so italic rows let text overflow.
            row = ROW.replace("overflow=hidden;", "") if "fontStyle=2" in extra else ROW
            rows.append((new_id("m"), html.escape(text), paint(row + extra, st, "row"), h, tp))
            texts.append((text, "fontStyle=2" in extra))
            return ROW_H

        for a in t["attrs"]:
            h += add_row(_member(a), "fontStyle=4;" if a["static"] else "",
                         mark("attribute", cls=name, name=a["name"]))
        for lit in t["literals"]:
            h += add_row(lit, "", mark("attribute", cls=name, name=lit))
        if (t["attrs"] or t["literals"]) and t["methods"]:
            rows.append((new_id("d"), "", DIVIDER, h, None))
            h += DIV_H
        for m in t["methods"]:
            extra = "fontStyle=4;" if m["static"] else ("fontStyle=2;" if m["abstract"] else "")
            h += add_row(_method(m), extra,
                         mark("method", cls=name, name=m["name"], arity=len(split_params(m["args"]))))
        w = max(w, max(_text_width(text, italic) for text, italic in texts))
        boxes[name] = (x, y, w, h)

        cells.append(cell(cid, label, style, f"{prefix}1",
                          f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />\n',
                          tooltip=tip))
        for rid, text, row_style, oy, tp in rows:
            rh = DIV_H if row_style.startswith("line;") else ROW_H
            cells.append(cell(rid, text, row_style, cid,
                              f'          <mxGeometry y="{oy}" width="{w}" height="{rh}" as="geometry" />\n',
                              tooltip=tp))

    ports = _Ports()
    for r in relations:
        reverse = r["arrow"] in REVERSED
        src, dst = (r["right"], r["left"]) if reverse else (r["left"], r["right"])
        scard, dcard = (r["rcard"], r["lcard"]) if reverse else (r["lcard"], r["rcard"])
        eid = new_id("e")
        status, tip = mark("relation", src=src, dst=dst, label=r["label"] or "") or (None, None)

        kept = layout.get("edges", {}).get(relation_key(src, dst, r["label"]))
        if kept:                                 # the person's own routing
            routing = _rebase(kept["style"], _drawn(layout, src, boxes), boxes[src],
                              _drawn(layout, dst, boxes), boxes[dst])
            points = kept["points"]
        else:                                    # nobody drew this line: find a clear path
            others = [b for n, b in boxes.items() if n not in (src, dst)]
            routing, points = ports.attach(src, dst, boxes[src], boxes[dst]), []
            if not routing or not segment_clear(_attached(routing, "exit", boxes[src]),
                                                _attached(routing, "entry", boxes[dst]), others):
                found = route(boxes[src], boxes[dst], list(boxes.values()))
                if found:
                    (ex, ey), (nx, ny), points = found
                    routing = f"exitX={ex};exitY={ey};entryX={nx};entryY={ny};"
                else:
                    routing = ""

        # Which side of each class the line meets decides where its end labels go.
        s_side = (_constraint_side(routing, "exit")
                  or _side(boxes[src], points[0] if points else _centre(boxes[dst])))
        d_side = (_constraint_side(routing, "entry")
                  or _side(boxes[dst], points[-1] if points else _centre(boxes[src])))

        geometry = '          <mxGeometry relative="1" as="geometry">\n'
        if points:
            geometry += ('            <Array as="points">\n'
                         + "".join(f'              <mxPoint x="{px}" y="{py}" />\n' for px, py in points)
                         + '            </Array>\n')
        geometry += '          </mxGeometry>\n'
        cells.append(cell(eid, "", paint(merge_styles(EDGE_STYLE[r["arrow"]], EDGE_BASE, routing), status, "edge"),
                          f"{prefix}1", geometry,
                          kind="edge", extra=f' source="{ids[src]}" target="{ids[dst]}"', tooltip=tip))
        # UML puts the role name (the member's name) and the multiplicity at the
        # end of the class that is referred to; the near end rarely carries one.
        cells += _end_labels(f"{eid}t", eid, d_side, "target", r["label"], dcard)
        cells += _end_labels(f"{eid}s", eid, s_side, "source", None, scard)
    return cells


def _drawn(layout, name, boxes):
    """A class's box as the person drew it (height too, when known)."""
    drawn = layout["classes"].get(name)
    if drawn is None or len(drawn) < 4 or not drawn[3]:
        return boxes[name]
    return drawn


def _rebase(style, old_src, new_src, old_dst, new_dst):
    """Keep attachment points where they were drawn when a box has grown.

    exitX/exitY (and entryX/entryY) are fractions of the box. A box that is now
    wider or taller would move them, so they are recomputed to keep the same
    absolute point — except on the right or bottom edge, which moves with the box.
    """
    parts = {k: v for k, _, v in (p.partition("=") for p in style.split(";")) if k}
    for end, old, new in (("exit", old_src, new_src), ("entry", old_dst, new_dst)):
        fx, fy = parts.get(f"{end}X"), parts.get(f"{end}Y")
        if fx is None or fy is None:
            continue
        fx, fy = float(fx), float(fy)
        if fx in (0.0, 1.0):                     # on the left or right edge: keep its height
            fy = min(max((old[1] + fy * old[3] - new[1]) / new[3], 0.05), 0.95)
        elif fy in (0.0, 1.0):                   # on the top or bottom edge: keep its x
            fx = min(max((old[0] + fx * old[2] - new[0]) / new[2], 0.05), 0.95)
        parts[f"{end}X"], parts[f"{end}Y"] = f"{fx:.4g}", f"{fy:.4g}"
    return "".join(f"{k}={v};" for k, v in parts.items())


def _attached(style, end, box):
    """The absolute point an exit/entry constraint attaches to."""
    x, y, w, h = box
    fx, fy = float(style_value(style, f"{end}X")), float(style_value(style, f"{end}Y"))
    return (x + fx * w, y + fy * h)


def _centre(box):
    x, y, w, h = box
    return (x + w / 2, y + h / 2)


def place(types, layout):
    """The design's layout, plus positions for classes it does not have.

    Returns (layout, spare_x). Classes the design lacks are stacked in a column
    right of the design, which also holds the legend on comparison pages.
    """
    classes = layout["classes"]
    right = max((box[0] + box[2] for box in classes.values()), default=0)
    spare_x = right + 80
    out, y = dict(classes), 260
    for name in types:
        if name not in out:
            out[name] = (spare_x, y, 300)
            y += 220
    return {"classes": out, "edges": layout.get("edges", {})}, spare_x


def document(types, relations, layout, name="Class diagram"):
    """A plain one-page .drawio of a class model — e.g. to start a new design."""
    return mxfile([(name, "page", build_cells(types, relations, place(types, layout)[0],
                                               prefix="page-"))])


# --------------------------------------------------------------------- comparison

def _marker(table):
    """Translate build_cells' description of an element into elements.py's keys."""
    def mark(category, **info):
        if category == "class":
            keys = [nname(info["name"])]
        elif category == "attribute":
            keys = [(nname(info["cls"]), nname(info["name"]))]
        elif category == "method":
            base = (nname(info["cls"]), nname(info["name"]))
            keys = [base, (base[0], f"{base[1]}/{info['arity']}")]
        else:
            keys = [(nname(info["src"]), nname(info["dst"]), nname(info["label"]))]
        for k in keys:
            if (category, k) in table:
                return table[(category, k)]
        return None
    return mark


def comparison(design_mmd, implemented_mmd, layout, result, design_label, implemented_label):
    """Both diagrams as a two-page .drawio document, colour-coded from `result`."""
    marks = status_marks(result, "NOT COUNTED\nThe design already implies this dependency "
                                 "through a method signature.")
    pages = [
        ("1 - Design (human)", design_mmd, "design", "DESIGN", design_label,
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("missing", f"Missing from the implementation ({len(result.missing)})")]),
        ("2 - Implemented (AI)", implemented_mmd, "implemented", "IMPLEMENTED DESIGN",
         implemented_label,
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("extra", f"Extra, not in the design ({len(result.extra)})")]
         + ([("uncounted", f"Not counted ({len(result.not_counted)})")]
            if result.not_counted else [])),
    ]
    out = []
    for name, path, pid, title, subtitle, key in pages:
        types, relations = parse(path.read_text())
        positions, spare_x = place(types, layout)
        cells = build_cells(types, relations, positions, prefix=f"{pid}-", mark=_marker(marks[pid]))
        cells += legend(f"{pid}-", title, subtitle, key, x=spare_x)
        out.append((name, pid, cells))
    return mxfile(out)
