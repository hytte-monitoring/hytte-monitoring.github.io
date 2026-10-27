# The class-diagram flow

Runs for every `diagrams/input/class.drawio`. The implementation is a CMake project in `impl/`
whose headers are in `impl/include/`.

| | File |
|---|---|
| Input | `diagrams/input/class.drawio`, `impl/` |
| Output | `diagrams/output/class-design.mmd` — the design, as mermaid |
| | `diagrams/output/class-implemented.mmd` — the implemented design, as mermaid |
| | `diagrams/output/class-comparison.drawio` — both, differences coloured |
| | `reports/class-report.md` — the report |

## 1. Reading `class.drawio`

draw.io has no UML layer: a class diagram is styled cells, and the meaning lives in the `style`
strings. [`drawio_read.py`](../class_diagram/drawio_read.py) recognises the shapes of draw.io's
UML class palette:

| Shape | Read as |
|---|---|
| a `swimlane` | a class; its label is the name, `Catalog<T>` gives a type parameter |
| a `«interface»`, `«enumeration»` or `«abstract»` line in the label | the kind |
| an italic class name (`fontStyle` bit 2) | abstract |
| the swimlane's child text rows | members, one per line: `+ name: Type`, `+ method(a: Type): Return` |
| an underlined row (`fontStyle` bit 4) | static |
| an italic method | abstract |
| a `line` row | the divider between attributes and methods; bare words above it are enum values |
| an edge between two classes, or their rows | a relation (see below) |
| an edge's child labels at `x < 0` / `x > 0` | labels at the source / target end: a multiplicity (`1`, `0..1`, `*`, `1..*`) or otherwise a role name |
| an edge's own label, in the middle | the role name, if no end carries one |

| Edge style | Relation |
|---|---|
| hollow `block` arrowhead | inheritance |
| hollow `block` arrowhead, dashed | realization |
| filled diamond (at either end) | composition — the diamond marks the owner |
| hollow diamond (at either end) | aggregation |
| `open` arrowhead | association |
| `open` arrowhead, dashed | dependency |

The reader also keeps how each line was routed — its waypoints and the points where it attaches
to its classes — so the comparison can redraw it the same way.

Compressed pages and `UserObject`-wrapped cells are handled. `fontStyle` is a bitmask, and
when a style repeats it the last one wins, as in draw.io. Labels are HTML inside an XML
attribute, so they are decoded twice. Anything unreadable becomes a warning in the report.

Not yet done: draw.io's own mermaid import stores the original mermaid in a `mermaidData`
attribute, which could be read directly when present.

## 2. Extracting the implemented design

[`cpp_extract.py`](../class_diagram/cpp_extract.py) parses every header under `impl/include/`
with libclang and applies [UML-CPP-MAPPING.md](UML-CPP-MAPPING.md) mechanically. It keeps only
declarations written in those headers (otherwise the whole standard library comes along),
drops the project's own namespace qualifiers, skips constructors, destructors and operators, and
classifies each field by its type: `unique_ptr` or by value = composition, `shared_ptr` =
aggregation, raw pointer or reference = association, containers = multiplicity `*`, `optional` =
`0..1`. A project type used only in a signature becomes a dependency.

## 3. Comparing

| Category | Identified by | Details compared |
|---|---|---|
| Class | name | kind, type parameter |
| Attribute (or enum value) | class + name | type, visibility, static |
| Method | class + name (+ arity for overloads) | parameter types, return type, visibility, static, abstract |
| Relation | source + target + role name | kind, far-end multiplicity |

The role name is part of a relation's identity because one pair of classes can carry two relations
of the same kind (`Loan *-- Date` as `dueDate` and as `returnedOn`). Kind is a detail, so an
association that became an aggregation is one *changed* relation, not one missing plus one extra.

**Names** compare case-insensitively, ignoring underscores and punctuation: `get_name`,
`getName` and `GetName` are the same. A different word is a different name: `getItemCount` is not
`itemCount`.

**Types** compare after normalization: `std::` dropped, `const`/`&`/`*` dropped, smart pointers
unwrapped, `std::vector<T>` → `list<T>`. See the table in UML-CPP-MAPPING.md.

**Implied dependencies are not counted.** Designers rarely draw a dependency arrow for every
parameter type, but the extractor records one. An extra dependency is therefore not counted when
the design has a method in the same class whose signature uses the target type. The report lists
it under *Not counted*, and the comparison drawing shows it grey.

## 4. The colour-coded comparison

`class-comparison.drawio` has two pages, *1 - Design (human)* and *2 - Implemented (AI)*, drawn
with the same shapes the reader recognises and the relation notation in
[UML-CPP-MAPPING.md](UML-CPP-MAPPING.md#drawing-relations).

- **Layout is the person's.** Classes keep their positions from `class.drawio`, and every line
  that is in the design keeps its routing. If a class has to grow to fit its text, attachment
  points keep their absolute position.
- **New lines are routed around classes.** A line nobody drew — one the AI added — is attached
  at header height or straight down when that path is clear, and otherwise routed by
  [`core/routing.py`](../core/routing.py): a grid search that treats every class as an obstacle
  and prefers few bends.
- **New classes go on the right,** stacked in a column under the legend.

Changed elements are amber on both pages, missing ones red on the design page, extra ones green
and not-counted ones grey on the implemented page. Each coloured element has a tooltip saying
what differs.
