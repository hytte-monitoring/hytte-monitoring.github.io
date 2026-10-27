"""C++ headers -> the implemented state machine of one class, via libclang.

Applies the state-machine rules of docs/UML-CPP-MAPPING.md mechanically:

    transition table   a static constexpr array member of the class whose element type
                       is a struct with two fields of the State enum (from, to), one of
                       the Event enum, and member-function pointers for the guard
                       (returns bool) and the action (returns void)
    states             the enumerators of that State enum, in declaration order
    events             the enumerators of that Event enum that the table uses; an
                       unused one becomes a warning
    initial state      the default member initializer of the class's first data
                       member of the State enum's type

extract(include_dir, subject) -> (machine, class name or None, warnings). The class is
the one whose name matches `subject` the way names compare everywhere: case and
underscores ignored.
"""
import clang.cindex as ci

from ..core.compare import nname
from ..core.cpp import translation_unit

K = ci.CursorKind


def extract(include_dir, subject):
    tu, ours = translation_unit(include_dir)
    machine = {"states": [], "initial": None, "transitions": [], "final": []}
    warnings = []

    cls = _find_class(tu.cursor, ours, subject)
    if cls is None:
        warnings.append(f"no class named like {subject!r} in the headers, so no state machine "
                        "could be read: every element of the design is missing")
        return machine, None, warnings
    name = cls.spelling

    table, fields = _find_table(cls)
    roles = state_enum = event_enum = None
    if table is None:
        warnings.append(f"{name} has no transition table: expected a static constexpr array of a "
                        "struct with from/event/to fields and guard/action member-function "
                        "pointers (UML-CPP-MAPPING.md, State machines); every transition is missing")
        state_enum, event_enum = _nested_enum(cls, "state"), _nested_enum(cls, "event")
    else:
        roles, state_enum, event_enum, problem = _roles(fields)
        if problem:
            warnings.append(f"{name}: {problem}; every transition is missing")
            table = None

    if state_enum is not None:
        machine["states"] = _enumerators(state_enum)
    else:
        warnings.append(f"{name} has no State enum, so no states could be read")

    if table is not None:
        rows = _rows(table)
        if not rows:
            warnings.append(f"{name}: the transition table is empty")
        for n, row in enumerate(rows, 1):
            t, problem = _transition(row, fields, roles, state_enum, event_enum)
            if problem:
                warnings.append(f"{name}: row {n} of the transition table was skipped: {problem}")
            else:
                machine["transitions"].append(t)

    if event_enum is not None:
        used = {nname(t["event"]) for t in machine["transitions"]}
        for ev in _enumerators(event_enum):
            if nname(ev) not in used:
                warnings.append(f"{name}: the event {ev!r} is declared but no transition uses it")

    if state_enum is not None:
        field, initial = _initial(cls, state_enum)
        if field is None:
            warnings.append(f"{name} has no data member of type {state_enum.spelling}, so the "
                            "initial state is unknown")
        elif initial is None:
            warnings.append(f"{name}: the state attribute {field.spelling!r} has no default member "
                            "initializer, so the initial state is unknown")
        else:
            machine["initial"] = initial
    return machine, name, warnings


# ------------------------------------------------------------------ finding things

def _find_class(root, ours, subject):
    want = nname(subject)

    def walk(cur):
        for c in cur.get_children():
            if c.kind == K.NAMESPACE:
                found = walk(c)
                if found is not None:
                    return found
            elif (c.kind in (K.CLASS_DECL, K.STRUCT_DECL) and ours(c) and c.is_definition()
                  and nname(c.spelling) == want):
                return c
        return None
    return walk(root)


def _enum_of(t):
    """The ENUM_DECL a type names, or None."""
    d = t.get_declaration()
    return d if d.kind == K.ENUM_DECL else None


def _enumerators(enum):
    return [c.spelling for c in enum.get_children() if c.kind == K.ENUM_CONSTANT_DECL]


def _nested_enum(cls, want):
    for c in cls.get_children():
        if c.kind == K.ENUM_DECL and nname(c.spelling) == want:
            return c
    return None


def _find_table(cls):
    """-> (VAR_DECL of the transition table, its row type's FIELD_DECLs) or (None, None).

    The table is a static data member (libclang: a VAR_DECL inside the class) holding a
    C array, or a std::array, of a struct with at least three enum-typed fields.
    """
    for c in cls.get_children():
        if c.kind != K.VAR_DECL:
            continue
        t = c.type
        if t.kind in (ci.TypeKind.CONSTANTARRAY, ci.TypeKind.INCOMPLETEARRAY):
            element = t.get_array_element_type()
        elif t.get_declaration().spelling == "array" and t.get_num_template_arguments() == 2:
            element = t.get_template_argument_type(0)
        else:
            continue
        row = element.get_declaration()
        if row.kind not in (K.STRUCT_DECL, K.CLASS_DECL):
            continue
        fields = [f for f in row.get_children() if f.kind == K.FIELD_DECL]
        if sum(1 for f in fields if _enum_of(f.type) is not None) >= 3:
            return c, fields
    return None, None


def _roles(fields):
    """-> ({field index: role}, State enum, Event enum, problem or None)"""
    by_enum = {}
    for i, f in enumerate(fields):
        e = _enum_of(f.type)
        if e is not None:
            by_enum.setdefault(e.get_usr(), []).append((i, e))
    twice = [v for v in by_enum.values() if len(v) == 2]
    once = [v for v in by_enum.values() if len(v) == 1]
    if len(twice) != 1 or len(once) != 1:
        return None, None, None, ("the transition row type should have two fields of the State "
                                  "enum (from, to) and one of the Event enum")
    (i_from, state_enum), (i_to, _) = twice[0]
    ((i_event, event_enum),) = once[0]
    roles = {i_from: "from", i_to: "to", i_event: "event"}
    for i, f in enumerate(fields):
        if f.type.kind == ci.TypeKind.MEMBERPOINTER:
            result = f.type.get_pointee().get_result().spelling
            roles[i] = "guard" if result == "bool" else "action"
    return roles, state_enum, event_enum, None


def _rows(table):
    """The initializer lists that are rows: nested lists whose entries are not lists."""
    rows = []

    def walk(c):
        if c.kind == K.INIT_LIST_EXPR:
            kids = list(c.get_children())
            if kids and all(k.kind != K.INIT_LIST_EXPR for k in kids):
                rows.append(kids)
                return
        for k in c.get_children():
            walk(k)
    walk(table)
    return rows


def _value(expr):
    """What an initializer expression names: ('enum', cursor), ('method', cursor),
    ('other', cursor), or None for nullptr / 0."""
    stack = [expr]
    while stack:
        c = stack.pop(0)
        if c.kind == K.DECL_REF_EXPR:
            r = c.referenced
            if r is not None and r.kind == K.ENUM_CONSTANT_DECL:
                return ("enum", r)
            if r is not None and r.kind in (K.CXX_METHOD, K.FUNCTION_DECL):
                return ("method", r)
            return ("other", c)
        if c.kind in (K.CXX_NULL_PTR_LITERAL_EXPR, K.INTEGER_LITERAL, K.GNU_NULL_EXPR):
            return None
        if c.kind in (K.MEMBER_REF_EXPR, K.LAMBDA_EXPR, K.CALL_EXPR):
            return ("other", c)
        stack = list(c.get_children()) + stack
    return None


def _transition(row, fields, roles, state_enum, event_enum):
    """One initializer row -> (transition, None) or (None, problem)."""
    t = {"from": None, "event": None, "guard": "", "action": "", "to": None}
    if len(row) > len(fields):
        return None, f"it has {len(row)} values for {len(fields)} fields"
    for i, expr in enumerate(row):
        role = roles.get(i)
        if role is None:
            continue
        value = _value(expr)
        if role in ("from", "to", "event"):
            want = state_enum if role != "event" else event_enum
            if value is None or value[0] != "enum" or value[1].semantic_parent.get_usr() != want.get_usr():
                return None, f"its {role} is not a value of {want.spelling}"
            t[role] = value[1].spelling
        elif value is not None:
            if value[0] != "method":
                return None, f"its {role} is not a pointer to a member function"
            t[role] = value[1].spelling
    for role in ("from", "event", "to"):
        if t[role] is None:
            return None, f"it has no {role}"
    return t, None


def _initial(cls, state_enum):
    """-> (the state attribute, the enumerator its initializer names or None), or (None, None).

    Without a default member initializer, a static constexpr member of the State type
    (`static constexpr State initial = State::Closed;`) is accepted instead.
    """
    field, initial = None, None
    for c in cls.get_children():
        if c.kind not in (K.FIELD_DECL, K.VAR_DECL):
            continue
        e = _enum_of(c.type)
        if e is None or e.get_usr() != state_enum.get_usr():
            continue
        value = _value(c)
        named = value[1].spelling if value and value[0] == "enum" else None
        if c.kind == K.FIELD_DECL and field is None:
            field, initial = c, named or initial
        elif c.kind == K.VAR_DECL and initial is None and named:
            initial = named
    return field, initial
