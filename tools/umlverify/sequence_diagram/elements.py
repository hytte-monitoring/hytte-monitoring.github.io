"""Sequence diagram -> elements, and the alignment of two message sequences.

    category    identified by                                   details compared
    lifeline    name (an object's class, or the actor's name)   (none)
    message     caller + receiver + method, in sequence          its place in the sequence

Messages have no identity of their own: the same call can occur twice, and one message
left out shifts every later one. So they are not matched by key like the elements of the
other diagram types but *aligned*: the longest common subsequence of the design's calls and
the implementation's calls is identical; a call left over on both sides with the same
caller, receiver and method is one *changed* message (it moved); the rest is missing or
extra. Return messages are documentation and take no part. A call a class makes to itself
that the design does not draw is not counted: a sequence diagram shows the collaboration
between objects, and a class's private helpers are its own business unless drawn.
"""
from ..core.compare import Element, Result, nname
from .mermaid import parse

COLUMNS = [("lifeline", "Lifelines"), ("message", "Messages")]


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def triple(m):
    return (nname(m["from"]), nname(m["to"]), nname(m["name"]))


def elements(mermaid_text):
    """-> ({(category, key): Element}, scenario). Message keys are (side-less) positions;
    align() pairs them."""
    scenario = parse(mermaid_text)
    found = {}
    for l in scenario["lifelines"]:
        found[("lifeline", nname(l["name"]))] = Element("lifeline", nname(l["name"]), l["name"],
                                                        f"{'actor' if l['kind'] == 'actor' else 'participant'} {l['name']}",
                                                        {})
    calls = [m for m in scenario["messages"] if m["kind"] == "call"]
    for n, m in enumerate(calls):
        found[("message", n)] = Element("message", n, f"{m['from']} → {m['to']} : {m['name']}()",
                                        f"{m['from']} ->> {m['to']} : {m['text']}", {})
    return found, scenario


def lcs_pairs(a, b):
    """Index pairs of a longest common subsequence of two lists of comparable items."""
    n, m = len(a), len(b)
    table = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            table[i][j] = (table[i + 1][j + 1] + 1 if a[i] == b[j]
                           else max(table[i + 1][j], table[i][j + 1]))
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def align(design, implemented):
    """(elements, scenario) of both sides -> a core.compare.Result."""
    d_elems, d_scenario = design
    i_elems, i_scenario = implemented
    counts = {c: {"design": 0, "implemented": 0, "identical": 0, "changed": 0, "missing": 0, "extra": 0}
              for c, _ in COLUMNS}
    changed, missing, extra, not_counted = [], [], [], []

    # lifelines: by name
    d_lines = {k[1]: e for k, e in d_elems.items() if k[0] == "lifeline"}
    i_lines = {k[1]: e for k, e in i_elems.items() if k[0] == "lifeline"}
    c = counts["lifeline"]
    for key in sorted(set(d_lines) | set(i_lines)):
        c["design"] += key in d_lines
        c["implemented"] += key in i_lines
        if key in d_lines and key in i_lines:
            c["identical"] += 1
        elif key in d_lines:
            c["missing"] += 1
            missing.append(d_lines[key])
        else:
            c["extra"] += 1
            extra.append(i_lines[key])

    # messages: by alignment
    d_msgs = sorted((k[1], e) for k, e in d_elems.items() if k[0] == "message")
    i_msgs = sorted((k[1], e) for k, e in i_elems.items() if k[0] == "message")
    d_calls = [m for m in d_scenario["messages"] if m["kind"] == "call"]
    i_calls = [m for m in i_scenario["messages"] if m["kind"] == "call"]
    drawn_self = {triple(m) for m in d_calls if triple(m)[0] == triple(m)[1]}
    counted = []
    for (n, e), m in zip(i_msgs, i_calls):
        t = triple(m)
        if t[0] == t[1] and t not in drawn_self:
            not_counted.append(e)
        else:
            counted.append((n, e, t))
    d_triples = [triple(m) for m in d_calls]
    i_triples = [t for _, _, t in counted]
    pairs = lcs_pairs(d_triples, i_triples)
    matched_d = {i for i, _ in pairs}
    matched_i = {j for _, j in pairs}

    def follows(elems, matched, at):
        """What the message at `at` follows: the nearest earlier matched message, or the start."""
        for k in range(at - 1, -1, -1):
            if k in matched:
                return elems[k][1].name
        return "the start"

    c = counts["message"]
    c["design"], c["implemented"], c["identical"] = len(d_msgs), len(counted), len(pairs)
    left_d = [i for i in range(len(d_msgs)) if i not in matched_d]
    left_i = [j for j in range(len(counted)) if j not in matched_i]
    for i in left_d:
        j = next((j for j in left_i if i_triples[j] == d_triples[i]), None)
        if j is None:
            c["missing"] += 1
            missing.append(d_msgs[i][1])
            continue
        left_i.remove(j)
        c["changed"] += 1
        changed.append((d_msgs[i][1], counted[j][1],
                        [("follows", follows(d_msgs, matched_d, i), follows(counted, matched_i, j))]))
    for j in left_i:
        c["extra"] += 1
        extra.append(counted[j][1])

    for c in counts.values():
        assert c["identical"] + c["changed"] + c["missing"] == c["design"]
        assert c["identical"] + c["changed"] + c["extra"] == c["implemented"]
    return Result(counts, changed, missing, extra, not_counted)
