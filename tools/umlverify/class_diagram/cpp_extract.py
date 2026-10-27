"""C++ headers -> the implemented class diagram, via libclang.

Applies docs/UML-CPP-MAPPING.md mechanically: no AI, no heuristics beyond what
that mapping specifies. extract(include_dir) returns the diagram as mermaid.
"""
import re

import clang.cindex as ci

from ..core.cpp import translation_unit

# Namespaces declared in the project's own headers; their qualifiers are dropped
# from type names (library::Member -> Member). Filled in by extract().
NAMESPACES = set()

PRIMITIVES = {"int", "bool", "double", "float", "char", "void", "size_t",
              "std::string", "std::size_t", "unsigned long", "long", "short"}
OWNING = {"std::unique_ptr": ("composition", "1"),
          "std::shared_ptr": ("aggregation", "1"),
          "std::weak_ptr": ("association", "1"),
          "std::optional": ("composition", "0..1")}
SEQUENCE = {"std::vector", "std::list", "std::set", "std::map", "std::deque"}


def strip_ns(t):
    for ns in NAMESPACES:
        t = re.sub(rf"\b{re.escape(ns)}::", "", t)
    return t


def clean(t):
    t = strip_ns(t)
    t = re.sub(r"\bconst\b", "", t).strip()
    t = t.rstrip("&").strip()
    return t


def template_of(t):
    m = re.match(r"^([\w:]+)<(.+)>$", t.strip())
    return (m.group(1), m.group(2).strip()) if m else (None, None)


def classify(type_spelling, project_types):
    """field type -> ('attr', type) | ('rel', kind, target, cardinality)"""
    # A reference member refers to an object it does not own, like a raw pointer.
    ref = re.sub(r"\bconst\b", "", strip_ns(type_spelling)).strip().endswith("&")
    t = clean(type_spelling)

    ptr = t.endswith("*") or ref
    if t.endswith("*"):
        t = t[:-1].strip()

    tmpl, arg = template_of(t)
    card = "1"
    kind = None

    if tmpl in SEQUENCE:
        card = "*"
        arg = arg.split(",")[-1].strip() if tmpl == "std::map" else arg
        inner_t, inner_arg = template_of(arg)
        if inner_t in OWNING:
            kind = OWNING[inner_t][0]
            t = clean(inner_arg)
        else:
            kind = "composition"
            t = clean(arg)
    elif tmpl in OWNING:
        kind, card = OWNING[tmpl]
        t = clean(arg)
    elif ptr:
        kind = "association"
    else:
        kind = "composition"

    base = t.split("<")[0]
    if base in project_types and project_types[base] != "enumeration":
        return ("rel", kind, base, card)
    return ("attr", strip_ns(type_spelling))


def extract(include_dir):
    """Every header under include_dir -> the implemented design, as mermaid."""
    NAMESPACES.clear()
    tu, ours = translation_unit(include_dir)

    # pass 1: what project types exist, and what shape are they
    decls = {}

    def collect(cur):
        for c in cur.get_children():
            if c.kind == ci.CursorKind.NAMESPACE:
                if ours(c):
                    NAMESPACES.add(c.spelling)
                collect(c)
                continue
            if not ours(c):
                continue
            if c.kind in (ci.CursorKind.CLASS_DECL, ci.CursorKind.STRUCT_DECL,
                          ci.CursorKind.CLASS_TEMPLATE, ci.CursorKind.ENUM_DECL):
                if c.is_definition() and c.spelling:
                    decls[c.spelling] = c
    collect(tu.cursor)

    shapes = {}
    for name, cur in decls.items():
        if cur.kind == ci.CursorKind.ENUM_DECL:
            shapes[name] = "enumeration"
            continue
        fields = [c for c in cur.get_children() if c.kind == ci.CursorKind.FIELD_DECL]
        methods = [c for c in cur.get_children() if c.kind == ci.CursorKind.CXX_METHOD]
        pure = [m for m in methods if m.is_pure_virtual_method()]
        has_vdtor = any(c.kind == ci.CursorKind.DESTRUCTOR and c.is_virtual_method()
                        for c in cur.get_children())
        if methods and len(pure) == len(methods) and not fields and has_vdtor:
            shapes[name] = "interface"
        elif pure and fields:
            shapes[name] = "abstract"
        else:
            shapes[name] = "class"

    VIS = {ci.AccessSpecifier.PUBLIC: "+", ci.AccessSpecifier.PROTECTED: "#",
           ci.AccessSpecifier.PRIVATE: "-"}

    types, relations = [], []
    for name, cur in decls.items():
        generic = None
        if cur.kind == ci.CursorKind.CLASS_TEMPLATE:
            tp = [c.spelling for c in cur.get_children()
                  if c.kind == ci.CursorKind.TEMPLATE_TYPE_PARAMETER]
            generic = tp[0] if tp else None

        attrs, methods, literals = [], [], []
        related = set()

        if cur.kind == ci.CursorKind.ENUM_DECL:
            literals = [c.spelling for c in cur.get_children()
                        if c.kind == ci.CursorKind.ENUM_CONSTANT_DECL]
        else:
            for c in cur.get_children():
                if c.kind == ci.CursorKind.CXX_BASE_SPECIFIER:
                    base = strip_ns(c.type.spelling).split("<")[0]
                    kind = "realization" if shapes.get(base) == "interface" else "inheritance"
                    relations.append((kind, name, base, "", "", ""))
                    related.add(base)
                elif c.kind == ci.CursorKind.FIELD_DECL:
                    label = c.spelling.rstrip("_")
                    r = classify(c.type.spelling, shapes)
                    if r[0] == "rel":
                        _, kind, target, card = r
                        relations.append((kind, name, target, "1", card, label))
                        related.add(target)
                    else:
                        attrs.append((VIS[c.access_specifier], label, strip_ns(r[1])))
                elif c.kind == ci.CursorKind.CXX_METHOD:
                    if c.spelling.startswith("operator"):
                        continue
                    params = [(strip_ns(p.type.spelling), p.spelling)
                              for p in c.get_arguments()]
                    methods.append((VIS[c.access_specifier], c.spelling, params,
                                    strip_ns(c.result_type.spelling),
                                    c.is_static_method(), c.is_pure_virtual_method()))

            # dependencies: project types used only in signatures
            for _, mname, params, ret, _, _ in methods:
                for t in [t for t, _ in params] + [ret]:
                    base = clean(t).split("<")[0].rstrip("*").strip()
                    inner = template_of(clean(t))[1]
                    for cand in filter(None, [base, clean(inner).split("<")[0] if inner else None]):
                        cand = cand.rstrip("*").strip()
                        if (cand in shapes and cand != name
                                and shapes[cand] != "enumeration"
                                and cand not in related):
                            relations.append(("dependency", name, cand, "", "", ""))
                            related.add(cand)

        types.append((name, shapes[name], generic, attrs, literals, methods))
    return to_mermaid(types, relations)


def canon(t):
    """C++ type spelling -> the canonical form the diagrams use.

    UML signatures do not show ownership plumbing: a `unique_ptr<Book>`
    parameter is a `Book` parameter. Ownership is expressed by the relation
    arrow, not by repeating the smart pointer in every method.
    """
    t = strip_ns(t).replace("std::", "")
    t = re.sub(r"\bconst\b", "", t).replace("&", "").replace("*", "").strip()
    t = re.sub(r"\s*<\s*", "<", re.sub(r"\s*>\s*", ">", t)).strip()
    for _ in range(4):
        collapsed = re.sub(r"\b(unique_ptr|shared_ptr|weak_ptr|optional)<(.+?)>", r"\2", t)
        if collapsed == t:
            break
        t = collapsed
    return re.sub(r"\s+", " ", t).replace("<", "~").replace(">", "~")


def to_mermaid(types, relations):
    ARROW = {"inheritance": "<|--", "realization": "<|..", "composition": "*--",
             "aggregation": "o--", "association": "-->", "dependency": "..>"}
    out = ["classDiagram", "    direction TB", ""]
    for name, kind, generic, attrs, literals, methods in types:
        title = f"{name}~{generic}~" if generic else name
        out.append(f"    class {title} {{")
        if kind in ("interface", "abstract", "enumeration"):
            out.append(f"        <<{kind}>>")
        for vis, n, t in attrs:
            out.append(f"        {vis}{canon(t)} {n}")
        for lit in literals:
            out.append(f"        {lit}")
        for vis, n, params, ret, static, pure in methods:
            ps = ", ".join(f"{canon(t)} {nm}".strip() for t, nm in params)
            mod = "$" if static else ("*" if pure else "")
            out.append(f"        {vis}{n}({ps}) {canon(ret)}{mod}")
        out.append("    }")
        out.append("")
    for kind, src, dst, sc, dc, label in relations:
        a = ARROW[kind]
        if kind in ("inheritance", "realization"):
            line = f"    {dst} {a} {src}"
        elif kind == "dependency":
            line = f"    {src} {a} {dst}"
        else:
            line = f'    {src} {a} "{dc}" {dst}' + (f" : {label}" if label else "")
        out.append(line)
    return "\n".join(out) + "\n"
