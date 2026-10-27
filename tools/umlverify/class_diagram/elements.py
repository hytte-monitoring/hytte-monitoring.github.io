"""Class diagram -> elements for core.compare.

    category    identified by                          details compared
    class       name                                   kind, type parameter
    attribute   class + name                           type, visibility, static
    method      class + name (+ arity for overloads)   parameter types, return type,
                                                       visibility, static, abstract
    relation    source + target + label                kind, cardinality

The label belongs in a relation's identity because one pair of classes can carry
two relations of the same kind (Loan *-- Date, as dueDate and returnedOn). Kind is
a detail, so association-became-aggregation is one *changed* relation.
"""
import re

from ..core.compare import Element, nname
from .mermaid import ARROW_KIND, KIND_ARROW, REVERSED, param_types, parse

COLUMNS = [("class", "Classes"), ("attribute", "Attributes"),
           ("method", "Methods"), ("relation", "Relations")]

VISIBILITY = {"+": "public", "-": "private", "#": "protected", "~": "package"}


def relation_key(source, target, label):
    """A relation's identity; source is the owning class (the child, for inheritance)."""
    return (nname(source), nname(target), nname(label or ""))


def ntype(t):
    """Type spellings compare after the normalization in docs/UML-CPP-MAPPING.md."""
    t = (t or "").strip().replace("std::", "")
    t = re.sub(r"\bconst\b", "", t).replace("&", "").replace("*", "").strip()
    t = t.replace("~", "<", 1)[::-1].replace("~", ">", 1)[::-1] if "~" in t else t
    t = re.sub(r"^(vector|list|set)<(.+)>$", r"list<\2>", t)
    t = re.sub(r"^(unique_ptr|shared_ptr|weak_ptr|optional)<(.+)>$", r"\2", t)
    key = nname(t)
    return {"": "void", "boolean": "bool", "int32t": "int", "unsignedlong": "sizet"}.get(key, key)


def _uml_type(t):
    """mermaid ~T~ -> <T>, for display."""
    return (t or "").replace("~", "<", 1)[::-1].replace("~", ">", 1)[::-1] if "~" in (t or "") else t


def elements(mermaid_text):
    """-> ({(category, key): Element}, types)"""
    types, relations = parse(mermaid_text)
    found = {}

    def add(e):
        found[(e.category, e.key)] = e

    for name, t in types.items():
        ck = nname(name)
        title = f"{name}<{t['generic']}>" if t["generic"] else name
        add(Element("class", ck, title,
                    f"class {title}" + (f" «{t['kind']}»" if t["kind"] != "class" else ""),
                    {"kind": (t["kind"], t["kind"]),
                     "type parameter": (t["generic"] or "", t["generic"] or "none")}))

        for a in t["attrs"]:
            add(Element("attribute", (ck, nname(a["name"])), f"{name}.{a['name']}",
                        f"{a['vis']}{_uml_type(a['type'])} {a['name']}{'$' if a['static'] else ''}",
                        {"type": (ntype(a["type"]), _uml_type(a["type"])),
                         "visibility": (a["vis"], VISIBILITY[a["vis"]]),
                         "static": (a["static"], "yes" if a["static"] else "no")}))
        for lit in t["literals"]:
            add(Element("attribute", (ck, nname(lit)), f"{name}.{lit}", lit, {}))

        seen = {}
        for m in t["methods"]:
            seen[nname(m["name"])] = seen.get(nname(m["name"]), 0) + 1
        for m in t["methods"]:
            ps = param_types(m["args"])
            mk = nname(m["name"])
            if seen[mk] > 1:                      # overloads: tell them apart by arity
                mk = f"{mk}/{len(ps)}"
            mod = "$" if m["static"] else ("*" if m["abstract"] else "")
            add(Element("method", (ck, mk), f"{name}.{m['name']}()",
                        f"{m['vis']}{m['name']}({', '.join(_uml_type(p) for p in ps)}) "
                        f"{_uml_type(m['ret'])}{mod}",
                        {"parameters": (tuple(ntype(p) for p in ps),
                                        f"({', '.join(_uml_type(p) for p in ps)})"),
                         "return type": (ntype(m["ret"]), _uml_type(m["ret"])),
                         "visibility": (m["vis"], VISIBILITY[m["vis"]]),
                         "static": (m["static"], "yes" if m["static"] else "no"),
                         "abstract": (m["abstract"], "yes" if m["abstract"] else "no")}))

    for r in relations:
        reverse = r["arrow"] in REVERSED
        src, dst = (r["right"], r["left"]) if reverse else (r["left"], r["right"])
        sc, dc = (r["rcard"], r["lcard"]) if reverse else (r["lcard"], r["rcard"])
        kind = ARROW_KIND[r["arrow"]]
        label = r["label"] or ""
        # Only the far end's multiplicity is compared. The near end ("how many
        # owners point here?") cannot be expressed by a C++ member, so the
        # extractor never states it and a design's value there is not checked.
        card = dc or ""
        add(Element("relation", relation_key(src, dst, label),
                    f"{src} → {dst}" + (f" ({label})" if label else ""),
                    f"{src} {KIND_ARROW[kind]} {dst}" + (f" : {label}" if label else ""),
                    {"kind": (kind, f"{kind} `{KIND_ARROW[kind]}`"),
                     "cardinality": (card, card or "none")}))

    return found, types


def implied_dependencies(types):
    """A not_counted rule for core.compare: dependencies the design already implies.

    The extractor records a dependency for every project type used only in a
    signature; designers rarely draw those. So an extra dependency is not counted
    when the design has a method in the same class whose signature uses the target.
    """
    classes = {nname(n) for n, t in types.items() if t["kind"] != "enumeration"}
    pairs = set()
    for name, t in types.items():
        for m in t["methods"]:
            for ty in param_types(m["args"]) + [m["ret"]]:
                for ident in re.findall(r"[A-Za-z_]\w*", ty):
                    if nname(ident) in classes and nname(ident) != nname(name):
                        pairs.add((nname(name), nname(ident)))

    def not_counted(e):
        return (e.category == "relation" and e.details["kind"][0] == "dependency"
                and (e.key[0], e.key[1]) in pairs)
    return not_counted
