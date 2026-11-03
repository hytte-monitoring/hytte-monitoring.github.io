# The state-machine flow

Runs for every `diagrams/input/state-<class>.drawio`: the state machine of one class, named by
the file's subject in lower case (`state-door.drawio` for `Door`, `state-library_item.drawio` for
`LibraryItem`). A project may have any number of these next to its `class.drawio`; they share
the implementation in `impl/`, which is built once per run.

| | File |
|---|---|
| Input | `diagrams/input/state-<class>.drawio`, `impl/` |
| Output | `diagrams/output/state-<class>-design.mmd` — the design, as mermaid |
| | `diagrams/output/state-<class>-implemented.mmd` — the implemented machine, as mermaid |
| | `diagrams/output/state-<class>-comparison.drawio` — both, differences coloured |
| | `reports/state-<class>-report.md` — the report |

## 1. Reading `state-<class>.drawio`

[`drawio_read.py`](../state_diagram/drawio_read.py) recognises the shapes of draw.io's UML
palette:

| Shape | Read as |
|---|---|
| a rounded rectangle (`rounded=1`) or `shape=umlState`, with a label | a state; the label is its name |
| the start symbol (`shape=startState`, or a black-filled ellipse without a label) | the initial pseudo-state |
| the end symbol (`shape=endState`) | the final pseudo-state |
| an edge from the start symbol to a state | the initial transition, `[*] --> S` |
| an edge from one state to another, or back to the same state | a transition; its label is `event [guard] / action`, guard and action optional |
| an unlabelled edge from a state to the end symbol | documentation that the state is terminal: kept in the drawing, not counted |

Labels are read the tolerant way: `lock[hasKey]/log()`, `lock [hasKey] / log` and
`lock [ hasKey ] / log()` are the same transition; parentheses after an event, a guard or an
action are dropped. A state's name may contain spaces (`In transit`); the mermaid text then
declares it as `state "In transit" as InTransit`.

Not supported, and reported as warnings: composite (nested) states, `entry /` and `exit /` lines
inside a state, history and choice pseudo-states, a labelled edge into the end symbol, a
transition without an event, a state drawn twice. As in the class flow, nothing unreadable is
dropped silently.

The reader also keeps how each line was routed and where its label sits, so the comparison can
redraw it the same way.

## 2. Extracting the implemented machine

[`cpp_extract.py`](../state_diagram/cpp_extract.py) parses the headers under `impl/include/`
with libclang, finds the class whose name matches the file's subject (case and underscores
ignored), and applies the *State machines* section of [UML-CPP-MAPPING.md](UML-CPP-MAPPING.md)
mechanically:

- **The table** is the class's first static data member that is an array (a C array or a
  `std::array`) of a struct with at least three enum-typed fields. The fields' roles come from
  their types: the two fields of one enum are `from` and `to`, in that order; the field of the
  other enum is the event; a member-function pointer returning `bool` is the guard, one returning
  `void` the action. Every row of the initializer is one transition; `nullptr` (or a missing
  trailing field) means no guard or no action.
- **States** are the enumerators of the `from`/`to` enum, in declaration order — including
  any that no transition uses.
- **Events** are the enumerators of the event enum that the table uses. A declared but unused
  event is a warning, not an element: a diagram has no place to draw an event on its own.
- **The initial state** is the default member initializer of the class's first data member of
  the State type (`State state_ = State::Closed;`), or else a static constexpr member of that
  type (`static constexpr State initial = State::Closed;`).

A class with no table, or a table whose rows do not fit, yields whatever could be read plus a
warning; the report then shows every transition as missing instead of failing. A class that does
not exist yields an empty machine: everything in the design is missing.

## 3. Comparing

| Category | Identified by | Details compared |
|---|---|---|
| State | name | — |
| Event | name | — |
| Transition | source state + event | target state, guard, action |
| Transition, when its state has several on that event | source state + event + guard | target state, action |
| The initial transition `[*] --> S` | one per machine | the state it enters |

The guard joins a transition's identity only when it must (`deliver [signed]` and
`deliver [refused]` from the same state are two transitions), so a guard the implementation
forgot is one *changed* transition, not one missing plus one extra. Names compare as everywhere:
case-insensitively, ignoring underscores, so `In transit` in the drawing is `InTransit` in C++,
and a guard drawn `[signed]` may be implemented as `signed_()` because `signed` is a C++ keyword.

## 4. The colour-coded comparison

`state-<class>-comparison.drawio` has the two pages of every comparison, *1 - Design (human)*
and *2 - Implemented (AI)*, drawn with the shapes the reader recognises.

- **Layout is the person's.** States keep their positions, and every transition the person drew
  keeps its routing and its label's position. An end symbol the person drew is shown on both
  pages, plain, next to its state.
- **New lines are routed around states.** A transition nobody drew gets a straight line when one
  is clear, spread out when several share a side, and otherwise a path found by
  [`core/routing.py`](../core/routing.py). Labels of lines running side by side are staggered
  along their lines so they do not land on each other. A self-transition loops over the
  top-right corner of its state.
- **New states go on the right,** in a column under the legend.
- **Events have no shape of their own**: they colour the transitions that use them, and are
  listed in the report.

Changed transitions are amber on both pages, missing states and transitions red on the design
page, extra ones green on the implemented page. Each coloured element has a tooltip saying what
differs. The same shapes are written by `drawio_write.document()`, which is how the examples'
`state-*.drawio` files were made.
