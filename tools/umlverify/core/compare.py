"""Element-by-element comparison of a design with an implemented design.

Diagram-agnostic. A diagram type turns each diagram into *elements* — for a class
diagram: classes, attributes, methods and relations — and this module puts every
element of either diagram into exactly one bucket:

    identical   in both, every detail matches
    changed     in both, at least one detail differs
    missing     in the design only
    extra       in the implementation only

Alignment = identical / (identical + changed + missing + extra). Deterministic:
the same two element sets always give the same result.
"""
import re
from typing import NamedTuple

BUCKETS = ("identical", "changed", "missing", "extra")


def nname(s):
    """Names compare case-insensitively, ignoring underscores and punctuation."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


class Element:
    """One countable thing in a diagram.

    category  which overview column it counts in, e.g. "class" or "relation"
    key       its identity within the category; equal keys = the same element
    name      how the report refers to it
    uml       how it is written in the diagram
    details   {detail: (normalized, display)}; normalized values are compared,
              display values are shown when they differ
    """

    def __init__(self, category, key, name, uml, details):
        self.category = category
        self.key = key
        self.name = name
        self.uml = uml
        self.details = details


class Result(NamedTuple):
    counts: dict        # {category: {"design", "implemented", *BUCKETS: int}}
    changed: list       # [(design element, implemented element, [(detail, design, implemented)])]
    missing: list       # [element]
    extra: list         # [element]
    not_counted: list   # [element] — extras the diagram type chose not to hold against the implementation


def compare(design, implemented, categories, not_counted=lambda element: False):
    """design, implemented: {(category, key): Element}.

    not_counted(element) is asked about each extra element; returning True leaves
    it out of every count (it is still reported, under "Not counted").
    """
    counts = {c: {"design": 0, "implemented": 0, **{b: 0 for b in BUCKETS}} for c in categories}
    changed, missing, extra = [], [], []
    skipped = [e for k, e in implemented.items() if k not in design and not_counted(e)]

    skip = {(e.category, e.key) for e in skipped}
    for key in sorted(set(design) | set(implemented) - skip, key=str):
        d, i = design.get(key), implemented.get(key)
        c = counts[(d or i).category]
        if d:
            c["design"] += 1
        if i:
            c["implemented"] += 1
        if d and i:
            diffs = [(name, d.details[name][1], i.details[name][1])
                     for name in d.details if d.details[name][0] != i.details[name][0]]
            if diffs:
                c["changed"] += 1
                changed.append((d, i, diffs))
            else:
                c["identical"] += 1
        elif d:
            c["missing"] += 1
            missing.append(d)
        else:
            c["extra"] += 1
            extra.append(i)

    for c in counts.values():   # every element counted exactly once
        assert c["identical"] + c["changed"] + c["missing"] == c["design"]
        assert c["identical"] + c["changed"] + c["extra"] == c["implemented"]
    return Result(counts, changed, missing, extra, skipped)


def totals(result):
    return {k: sum(c[k] for c in result.counts.values())
            for k in ("design", "implemented", *BUCKETS)}


def alignment(counts):
    total = sum(counts[b] for b in BUCKETS)
    return 100.0 * counts["identical"] / total if total else 100.0
