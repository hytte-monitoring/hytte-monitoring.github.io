# The sequence-diagram flow

Runs for every `diagrams/input/sequence-<scenario>.drawio`: one scenario, drawn as a sequence
diagram, and implemented as a small program in `impl/scenarios/<scenario>.cpp`. A project may
have any number of scenarios next to its `class.drawio` and its state machines; they share the
implementation in `impl/`.

Unlike the other flows, the implemented diagram is not *read* from the code but *recorded*
from it: the scenario runs, every call between the project's classes is written down as it
happens, and the calls in order are the messages. A method body can be written a hundred ways,
but the calls it makes are what a sequence diagram shows, and a run shows them exactly.

| | File |
|---|---|
| Input | `diagrams/input/sequence-<scenario>.drawio`, `impl/` with `impl/scenarios/<scenario>.cpp` |
| Output | `diagrams/output/sequence-<scenario>-design.mmd` — the design, as mermaid |
| | `diagrams/output/sequence-<scenario>-implemented.mmd` — the recorded scenario, as mermaid |
| | `diagrams/output/sequence-<scenario>-comparison.drawio` — both, differences coloured |
| | `reports/sequence-<scenario>-report.md` — the report |
| Working files | `build-trace/` — the traced build, and `build-trace/traces/<scenario>.txt` |

## 1. Reading `sequence-<scenario>.drawio`

[`drawio_read.py`](../sequence_diagram/drawio_read.py) recognises the shapes of draw.io's
UML palettes:

| Shape | Read as |
|---|---|
| a lifeline (`shape=umlLifeline`, any participant style) | a lifeline named by its label: `order: Order`, `:Order` and `Order` are all `Order` |
| an actor lifeline (`participant=umlActor`), or a standalone `shape=umlActor` | an actor, named by its label |
| an activation bar (`perimeter=orthogonalPerimeter`) on a lifeline | part of that lifeline: messages may attach to it |
| an edge between two lifelines, directly or through their activations | a message: dashed is a return, anything else a call; the label names the method, `lend(b1, m1)` |
| an edge attached to nothing | placed on the lifelines nearest to its end points |
| a fragment (`shape=umlFrame`: alt, loop, opt) | not supported, a warning; the messages inside are read in order like the others |

Messages are ordered by their height on the page. draw.io keeps a message's height in a
waypoint, an entry or exit point, or an end point, depending on how it was drawn; the reader
takes whichever is there. Two lifelines of the same class cannot be told apart (objects are
identified by class), so the second becomes a warning. Creation messages (`«create»`, `new`)
and calls without a label are warnings too: constructors are never messages.

The **initiator** is the actor, or the leftmost lifeline when there is no actor. Its messages
are the calls the scenario makes from outside every class.

## 2. Recording the implemented scenario

[`core/project.py`](../core/project.py) builds `impl/` a second time, in `build-trace/`, with
the project's own `CMakeLists.txt` and one addition: [`runtime/instrument.cmake`](../runtime/instrument.cmake)
is included after its `project()` call, so every source is compiled with
`-finstrument-functions -g -O0` and the tiny runtime [`runtime/uml_trace.cpp`](../runtime/uml_trace.cpp)
is linked into every executable. The runtime appends one line per function entry and exit to
the file named by `UML_TRACE_FILE` — addresses only, nothing else happens. The traced build is
rebuilt from scratch on every run, so a recording always comes from the sources as they are.

[`trace_extract.py`](../sequence_diagram/trace_extract.py) then runs `scenario_<scenario>`
from that build, resolves the addresses with the executable's symbol table (`nm`, see
[`core/trace.py`](../core/trace.py)), and reads the messages off the entries and exits by the
rules in the *Sequence diagrams* section of [UML-CPP-MAPPING.md](UML-CPP-MAPPING.md):

- Only calls made while the scenario's `scenario()` function runs count. `main()` sets the
  objects up; that is not part of the diagram.
- A **message** is the entry of a method of one of the project's classes (the classes the
  headers declare, found with libclang). Its receiver is that class — the object's actual
  class, whatever the static type of the pointer or reference it was called through.
- Its **caller** is the class of the nearest enclosing project method on the call stack; code
  in a lambda counts as the method the lambda is written in. A call from outside every class
  comes from the initiator.
- Constructors, destructors, operators, free functions and the standard library are not
  messages; a call the stack passes through them is attributed to the nearest class above.

Objects are told apart by class: one lifeline per class. The design's initiator lends its
name to the recorded scenario.

## 3. Comparing

| Category | Identified by | Details compared |
|---|---|---|
| Lifeline | name | — |
| Message | caller + receiver + method, in sequence | its place in the sequence |

Messages have no identity of their own — the same call can occur twice, and one message left
out shifts every later one — so they are not matched by key but **aligned**
([`elements.py`](../sequence_diagram/elements.py)): the longest common subsequence of the
design's calls and the recorded calls is *identical*; a call left over on both sides with the
same caller, receiver and method is one *changed* message, reported with what it follows on
each side; the rest is *missing* or *extra*. Return messages are documentation: drawn,
written to the mermaid text, never compared.

**Undrawn self-calls are not counted.** A call a class makes to itself (`Library` calling its
own `nextLoanId()`) that the design does not draw is listed under *Not counted* and shown
grey: a sequence diagram shows the collaboration between objects, and a class's private
helpers are its own business unless the design draws them — a drawn self-message must then
happen. Every call *between* classes counts, getters included: if the implementation asks a
`Book` for its title, the diagram should say so, or the code should not.

## 4. The colour-coded comparison

`sequence-<scenario>-comparison.drawio` has the two pages of every comparison. Lifelines keep
their positions from the design and the design page keeps its messages' heights; the
implemented page spaces its messages evenly. Lifelines the design lacks go to the right of
the others; a self-message is a small loop. There are no activation bars: the messages and
their order are what is verified. Missing lifelines and messages are red on the design page,
extra ones green and not-counted ones grey on the implemented page, and a message that moved
is amber on both, with a tooltip saying what it follows on each side.

`drawio_write.document()` writes the same shapes, which is how the examples' `sequence-*.drawio`
files were made.
