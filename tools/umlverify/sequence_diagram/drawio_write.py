"""scenario -> draw.io shapes, and the colour-coded comparison.

Writes the shapes drawio_read.py recognises: lifelines (an actor lifeline for the actor),
call messages with a filled arrowhead, return messages dashed, self-messages as a small loop.
Every message attaches to its two lifelines at an explicit height, which is how draw.io keeps
a message where it was drawn.

The comparison has two pages, like the others:

    1 - Design (human)       changed elements amber, missing elements red
    2 - Implemented (AI)     changed elements amber, extra elements green,
                             calls a class makes to itself that the design does not draw grey

Lifelines keep their positions from the design and the design page keeps its messages'
heights; lifelines the design lacks go to the right of the others. There are no activation
bars: the messages and their order are what is verified.
"""
import html

from ..core.compare import nname
from ..core.drawio import cell, legend, mxfile, paint, status_marks
from .mermaid import parse

LIFELINE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;"
            "dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;"
            "size=40;")
ACTOR = ("shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;"
         "html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;verticalAlign=top;"
         "spacingTop=36;outlineConnect=0;portConstraint=eastwest;size=40;")
CALL = "html=1;verticalAlign=bottom;labelBackgroundColor=none;endArrow=block;endFill=1;curved=0;rounded=0;"
RETURN = ("html=1;verticalAlign=bottom;labelBackgroundColor=none;endArrow=open;endFill=0;endSize=8;"
          "dashed=1;curved=0;rounded=0;")
HEAD, WIDTH, ACTOR_WIDTH, GAP, TOP, FIRST, ROW, LOOP = 40, 100, 30, 60, 40, 70, 40, 24


def _width(name, kind):
    return ACTOR_WIDTH if kind == "actor" else max(WIDTH, int(len(name) * 7.5) + 24)


def place(scenario, layout):
    """Lifeline boxes for every lifeline of the scenario: the design's where it has one, the
    rest to the right. Returns ({name: (x, y, w, h)}, legend x)."""
    drawn = {nname(n): box for n, box in layout.get("lifelines", {}).items()}
    right = max((b[0] + b[2] for b in drawn.values()), default=TOP - GAP)
    top = min((b[1] for b in drawn.values()), default=TOP)
    boxes = {}
    for l in scenario["lifelines"]:
        box = drawn.get(nname(l["name"]))
        if box is None:
            w = _width(l["name"], l["kind"])
            box = (right + GAP, top, w, 0)
            right += GAP + w
        boxes[l["name"]] = box
    return boxes, right + 80


def _heights(scenario, layout, boxes):
    """The y of every message: the design's own where known, else evenly spaced."""
    top = min((b[1] for b in boxes.values()), default=TOP)
    known = layout.get("messages") or {}
    ys, y = [], top + HEAD + FIRST
    for i, m in enumerate(scenario["messages"]):
        if i in known:
            y = known[i]
        ys.append(y)
        y += ROW + (LOOP if m["from"] == m["to"] else 0)
    return ys


def build_cells(scenario, layout, prefix="", mark=None):
    """Scenario -> draw.io cells. mark(category, **info) may return (status, tooltip):
    mark("lifeline", name=...), mark("message", index=n) with n counting calls only."""
    mark = mark or (lambda category, **info: None)
    cells, ids = [], {}
    boxes, _ = place(scenario, layout)
    ys = _heights(scenario, layout, boxes)
    bottom = max(ys, default=TOP + HEAD + FIRST) + ROW + LOOP

    for n, l in enumerate(scenario["lifelines"]):
        x, y, w, h = boxes[l["name"]]
        h = max(h, bottom - y)
        boxes[l["name"]] = (x, y, w, h)
        lid = f"{prefix}l{n}"
        ids[l["name"]] = lid
        status, tip = mark("lifeline", name=l["name"]) or (None, None)
        style = paint(ACTOR if l["kind"] == "actor" else LIFELINE, status, "shape")
        cells.append(cell(lid, html.escape(l["name"]), style, f"{prefix}1",
                          f'          <mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" as="geometry" />\n',
                          tooltip=tip))

    call_index = 0
    for i, m in enumerate(scenario["messages"]):
        y = ys[i]
        status, tip = (None, None)
        if m["kind"] == "call":
            status, tip = mark("message", index=call_index) or (None, None)
            call_index += 1
        sx, sy, sw, sh = boxes[m["from"]]
        dx, dy, dw, dh = boxes[m["to"]]
        style = RETURN if m["kind"] == "return" else CALL
        points = ""
        if m["from"] == m["to"]:                   # a self-message: a small loop to the right
            cx = sx + sw / 2
            style += (f"exitX=0.5;exitY={(y - sy) / sh:.4f};exitPerimeter=0;"
                      f"entryX=0.5;entryY={(y + LOOP - sy) / sh:.4f};entryPerimeter=0;"
                      "align=left;verticalAlign=middle;")
            points = ('            <Array as="points">\n'
                      f'              <mxPoint x="{cx + 40:g}" y="{y:g}" />\n'
                      f'              <mxPoint x="{cx + 40:g}" y="{y + LOOP:g}" />\n'
                      '            </Array>\n'
                      '            <mxPoint x="8" y="0" as="offset" />\n')   # label right of the loop
        else:
            style += (f"exitX=0.5;exitY={(y - sy) / sh:.4f};exitPerimeter=0;"
                      f"entryX=0.5;entryY={(y - dy) / dh:.4f};entryPerimeter=0;")
        cells.append(cell(f"{prefix}m{i}", html.escape(m["text"]), paint(style, status, "edge"),
                          f"{prefix}1",
                          '          <mxGeometry relative="1" as="geometry">\n' + points
                          + '          </mxGeometry>\n',
                          kind="edge", extra=f' source="{ids[m["from"]]}" target="{ids[m["to"]]}"',
                          tooltip=tip))
    return cells


def document(scenario, layout=None, name="Sequence diagram"):
    """A plain one-page .drawio of a scenario — e.g. to start a new design."""
    return mxfile([(name, "page", build_cells(scenario, layout or {}, prefix="page-"))])


# --------------------------------------------------------------------- comparison

def _marker(table):
    def mark(category, **info):
        key = nname(info["name"]) if category == "lifeline" else info["index"]
        return table.get((category, key))
    return mark


def comparison(design_mmd, implemented_mmd, layout, result, design_label, implemented_label):
    """Both scenarios as a two-page .drawio document, colour-coded from `result`."""
    marks = status_marks(result, "NOT COUNTED\nA call the class makes to itself that the "
                                 "design does not draw.")
    pages = [
        ("1 - Design (human)", design_mmd, "design", "DESIGN", design_label, layout,
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("missing", f"Missing from the implementation ({len(result.missing)})")]),
        ("2 - Implemented (AI)", implemented_mmd, "implemented", "IMPLEMENTED SCENARIO",
         implemented_label, {"lifelines": layout.get("lifelines", {})},
         [(None, "Identical"),
          ("changed", f"Changed ({len(result.changed)})"),
          ("extra", f"Extra, not in the design ({len(result.extra)})")]
         + ([("uncounted", f"Not counted ({len(result.not_counted)})")]
            if result.not_counted else [])),
    ]
    out = []
    for name, path, pid, title, subtitle, page_layout, key in pages:
        scenario = parse(path.read_text())
        _, legend_x = place(scenario, page_layout)
        cells = build_cells(scenario, page_layout, prefix=f"{pid}-", mark=_marker(marks[pid]))
        cells += legend(f"{pid}-", title, subtitle, key, x=legend_x)
        out.append((name, pid, cells))
    return mxfile(out)
