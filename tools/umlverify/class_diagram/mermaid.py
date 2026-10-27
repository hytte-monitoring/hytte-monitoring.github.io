"""Read and write the mermaid `classDiagram` subset used by the class-diagram flow.

A model is two things:

    types      {name: {"name", "generic", "kind", "attrs", "methods", "literals"}}
    relations  [{"left", "lcard", "arrow", "rcard", "right", "label"}]

`kind` is class, abstract, interface or enumeration. Types are written the
mermaid way throughout: `vector~T~`, parameters as `Type name`.
"""
import re

ARROW_KIND = {"<|--": "inheritance", "<|..": "realization", "*--": "composition",
              "o--": "aggregation", "-->": "association", "..>": "dependency"}
KIND_ARROW = {v: k for k, v in ARROW_KIND.items()}

# For these arrows the diagram is written parent-first (`Base <|-- Derived`),
# so the right-hand class is the one the relation starts from.
REVERSED = {"<|--", "<|.."}


def split_params(args):
    """'map~K, V~ m, int n' -> ['map~K, V~ m', 'int n'], respecting generics."""
    parts, depth, cur = [], 0, ""
    for ch in args:
        depth += (ch == "<") - (ch == ">")
        if ch == "," and depth == 0 and cur.count("~") % 2 == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def param_types(args):
    return [p.rsplit(" ", 1)[0] if " " in p else p for p in split_params(args)]


def parse(text):
    types, relations = {}, []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%") or line == "classDiagram" or line.startswith("direction"):
            continue

        if current is not None and line == "}":
            current = None
            continue

        m = re.match(r"^class\s+([A-Za-z_]\w*)(?:~(\w+)~)?\s*\{$", line)
        if m:
            current = {"name": m.group(1), "generic": m.group(2), "kind": "class",
                       "attrs": [], "methods": [], "literals": []}
            types[current["name"]] = current
            continue

        if current is not None:
            m = re.match(r"^<<(\w+)>>$", line)
            if m:
                current["kind"] = m.group(1)
                continue
            # method:  +name(args) ret    with optional trailing $ (static) or * (abstract)
            m = re.match(r"^([+\-#~])(\w+)\((.*?)\)\s*(.*?)([$*])?$", line)
            if m:
                vis, name, args, ret, mod = m.groups()
                current["methods"].append(
                    {"vis": vis, "name": name, "args": args, "ret": ret or "void",
                     "static": mod == "$", "abstract": mod == "*"})
                continue
            # attribute:  +type name      with optional trailing $
            m = re.match(r"^([+\-#~])([\w:~<>, ]+?)\s+(\w+)([$*])?$", line)
            if m:
                vis, typ, name, mod = m.groups()
                current["attrs"].append(
                    {"vis": vis, "type": typ, "name": name, "static": mod == "$"})
                continue
            # bare enumeration literal
            if re.match(r"^\w+$", line):
                current["literals"].append(line)
            continue

        m = re.match(
            r'^([A-Za-z_]\w*)\s*(?:"([^"]+)"\s*)?'
            r"(<\|--|<\|\.\.|\*--|o--|-->|\.\.>)"
            r'\s*(?:"([^"]+)"\s*)?([A-Za-z_]\w*)\s*(?::\s*(.+))?$',
            line)
        if m:
            left, lcard, arrow, rcard, right, label = m.groups()
            relations.append({"left": left, "lcard": lcard, "arrow": arrow,
                              "rcard": rcard, "right": right, "label": label})
    return types, relations


def write(types, relations, header=()):
    out = [f"%% {line}" for line in header] + ["classDiagram", "    direction TB", ""]
    for name, t in types.items():
        title = f"{name}~{t['generic']}~" if t["generic"] else name
        out.append(f"    class {title} {{")
        if t["kind"] != "class":
            out.append(f"        <<{t['kind']}>>")
        for a in t["attrs"]:
            out.append(f"        {a['vis']}{a['type']} {a['name']}{'$' if a['static'] else ''}")
        for lit in t["literals"]:
            out.append(f"        {lit}")
        for m in t["methods"]:
            mod = "$" if m["static"] else ("*" if m["abstract"] else "")
            out.append(f"        {m['vis']}{m['name']}({m['args']}) {m['ret']}{mod}")
        out += ["    }", ""]
    for r in relations:
        lcard = f' "{r["lcard"]}"' if r["lcard"] else ""
        rcard = f'"{r["rcard"]}" ' if r["rcard"] else ""
        out.append(f"    {r['left']}{lcard} {r['arrow']} {rcard}{r['right']}"
                   + (f" : {r['label']}" if r["label"] else ""))
    return "\n".join(out) + "\n"
