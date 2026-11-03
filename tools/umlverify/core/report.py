"""The verification report, as markdown.

Diagram-agnostic layout: a link to the colour-coded comparison, the two sources,
an overview table with a legend, then every changed, missing and extra element.
The diagram type supplies its vocabulary through a ReportText.
"""
from typing import NamedTuple

from .compare import alignment, totals


class ReportText(NamedTuple):
    title: str             # e.g. "Class diagram verification report"
    columns: list          # [(category, column title)], in overview order
    element: str           # what one element is, e.g. "one class, one attribute, …"
    details: str           # what "every detail matches" covers
    implemented_by: str    # how the implemented design was made, markdown
    not_counted: str = ""  # why the not-counted elements are not counted


def render(result, text, sources, comparison, warnings=()):
    """sources: {"design": md, "implemented": md} — markdown for the two File cells.
    comparison: path of the comparison .drawio, relative to the report."""
    categories = [c for c, _ in text.columns]
    counts, total = result.counts, totals(result)
    score = alignment(total)
    distinct = sum(total[b] for b in ("identical", "changed", "missing", "extra"))

    def order(e):
        return (categories.index(e.category), e.name.lower())

    def row(label, key):
        return (f"| {label} | " + " | ".join(str(counts[c][key]) for c in categories)
                + f" | **{total[key]}** |")

    out = [
        f"# {text.title}",
        "",
        f"**🎨 [Open the colour-coded comparison in draw.io]({comparison})** — "
        "page 1 is the design, page 2 the implementation. Every difference below is coloured "
        "there; hover over a coloured element to see what differs.",
        "",
        "| | File | Made by |",
        "|---|---|---|",
        f"| **Design** | {sources['design']} | a person, in draw.io |",
        f"| **Implemented design** | {sources['implemented']} | {text.implemented_by} |",
        "",
        "> In VS Code, click a link to open the file. `.drawio` files open in the "
        "*Draw.io Integration* extension, which VS Code offers to install for this repository.",
        "",
        "## Overview",
        "",
        f"**Alignment: {score:.1f} %** — {total['identical']} of the {distinct} elements "
        "that appear in either diagram are identical in both.",
        "",
        "| | " + " | ".join(title for _, title in text.columns) + " | **Total** |",
        "|---|" + "--:|" * (len(categories) + 1),
        row("In design", "design"),
        row("In implemented design", "implemented"),
        row("✅ Identical", "identical"),
        row("✏️ Changed", "changed"),
        row("➖ Missing", "missing"),
        row("➕ Extra", "extra"),
        "| **Alignment** | " + " | ".join(f"{alignment(counts[c]):.1f} %" for c in categories)
        + f" | **{score:.1f} %** |",
        "",
        "### What the numbers mean",
        "",
        "| | Meaning |",
        "|---|---|",
        "| **In design** | Elements drawn in the design. |",
        "| **In implemented design** | Elements found in the implementation. |",
        f"| **✅ Identical** | In both, and every detail matches: {text.details}. |",
        "| **✏️ Changed** | In both, but at least one detail differs. |",
        "| **➖ Missing** | In the design, absent from the implementation. The AI left it out. |",
        "| **➕ Extra** | In the implementation, absent from the design. The AI added it. |",
        "| **Alignment** | Identical ÷ (Identical + Changed + Missing + Extra). "
        "100 % means the implementation is exactly the design. |",
        "",
        f"An *element* is {text.element}. "
        "Every element is counted exactly once, so the table adds up: "
        "Identical + Changed + Missing = In design, and "
        "Identical + Changed + Extra = In implemented design. "
        "Every Changed, Missing and Extra element is listed below.",
        "",
        "## Differences",
        "",
        f"### ✏️ Changed ({len(result.changed)})",
        "",
    ]
    if result.changed:
        out += ["| Element | What differs | Design | Implemented |", "|---|---|---|---|"]
        for d, _, diffs in sorted(result.changed, key=lambda x: order(x[0])):
            for n, (detail, dv, iv) in enumerate(diffs):
                label = f"{d.category} `{d.name}`" if n == 0 else ""
                out.append(f"| {label} | {detail} | {dv} | {iv} |")
    else:
        out.append("_None._")
    out.append("")

    for heading, items, column in (("➖ Missing", result.missing, "As drawn in the design"),
                                   ("➕ Extra", result.extra, "As found in the implementation")):
        out += [f"### {heading} ({len(items)})", ""]
        if items:
            out += [f"| Element | {column} |", "|---|---|"]
            out += [f"| {e.category} `{e.name}` | `{e.uml}` |" for e in sorted(items, key=order)]
        else:
            out.append("_None._")
        out.append("")

    if result.not_counted:
        out += ["### Not counted", "", text.not_counted, ""]
        out += [f"- {e.category} `{e.uml}`" for e in sorted(result.not_counted, key=order)]
        out.append("")

    if warnings:
        out += [f"### ⚠️ Warnings ({len(warnings)})", "",
                "Things that could not be read or counted, in the design or in the "
                "implementation. They are not in any count above, so check them by hand.", ""]
        out += [f"- {w}" for w in warnings]
        out.append("")

    out += ["---", "",
            "_Generated by `tools/verify.py`. Deterministic: the same two diagrams "
            "always produce this exact report._", ""]
    return "\n".join(out)
