# umlverify

A Python library that checks an implementation against a UML design drawn in draw.io, and
reports every difference. It is deterministic — no AI anywhere — so the same design and the same
code always give the same report. [`tools/verify.py`](../../verify.py) is its command line; the
VS Code task *Verify design* runs that.

## How a verification works

```
diagrams/input/<type>.drawio ──read──▶ design model ────────────┐
                                                                 ├─ compare ─▶ reports/<type>-report.md
impl/ ──build──▶ extract ──────────▶ implemented model ──────────┘             diagrams/output/<type>-comparison.drawio
```

1. **Read the design.** The draw.io file is turned into a model, which is also written out as
   mermaid (`diagrams/output/<type>-design.mmd`).
2. **Build and extract the implementation.** The code must build; the implemented design is then
   read from it mechanically, by libclang: for class diagrams from the C++ headers, for state
   machines from the class's transition table. A sequence diagram is recorded instead of read:
   the scenario runs in a traced build and its calls are the messages.
3. **Compare.** Both models become *elements* — for a class diagram, one class, attribute, method
   or relation each — and every element of either diagram lands in exactly one bucket:

   | Bucket | Meaning |
   |---|---|
   | ✅ Identical | in both, every detail matches |
   | ✏️ Changed | in both, at least one detail differs |
   | ➖ Missing | in the design only — the AI left it out |
   | ➕ Extra | in the implementation only — the AI added it |

   **Alignment = Identical ÷ (Identical + Changed + Missing + Extra)**, per category and in total,
   with no weights. The counts must add up (Identical + Changed + Missing = In design) and the
   library asserts that they do.
4. **Report.** A markdown report (overview table, legend, every difference) and a two-page
   draw.io comparison with every difference coloured, both from the same comparison result, so
   they cannot disagree.

The **input file's name picks the diagram type**: `class.drawio` runs the class-diagram flow,
`state-<class>.drawio` (say `state-order.drawio`) the state-machine flow for that class, and
`sequence-<scenario>.drawio` the sequence-diagram flow for that scenario. All outputs carry the
file's name as a prefix, so several designs share one folder and one implementation, which is
built once per run.

## Package layout

```
umlverify/
  __init__.py          FLOWS: input file name -> flow
  core/                diagram-agnostic
    drawio.py            read pages, cells and edge routing; write cells, legends, documents;
                         status colours
    compare.py           Element, the four buckets, alignment
    report.py            the markdown report
    routing.py           orthogonal routing around boxes, for lines nobody drew
    project.py           Context (a project's paths), FlowFailed/NotReady, the CMake build gate,
                         the traced build
    cpp.py               parsing a project's headers with libclang
    trace.py             function traces: recording a run, resolving addresses to names
  class_diagram/       the class-diagram flow: class.drawio + C++
    __init__.py          run(): read → build → extract → compare → report
    drawio_read.py       class.drawio -> model
    drawio_write.py      model -> draw.io shapes; the colour-coded comparison
    mermaid.py           the mermaid classDiagram subset, read and written
    cpp_extract.py       C++ headers -> model, via libclang
    elements.py          model -> elements; C++-aware type normalization
  state_diagram/       the state-machine flow: state-<class>.drawio + C++
    __init__.py          run(), the same four steps
    drawio_read.py       state-<class>.drawio -> machine
    drawio_write.py      machine -> draw.io shapes; the colour-coded comparison
    mermaid.py           the mermaid stateDiagram-v2 subset, read and written
    cpp_extract.py       the class's transition table -> machine, via libclang
    elements.py          machine -> elements
  sequence_diagram/    the sequence-diagram flow: sequence-<scenario>.drawio + a scenario program
    __init__.py          run(): read → build (twice) → record → align → report
    drawio_read.py       sequence-<scenario>.drawio -> scenario
    drawio_write.py      scenario -> draw.io shapes; the colour-coded comparison
    mermaid.py           the mermaid sequenceDiagram subset, read and written
    trace_extract.py     a run of the scenario -> the messages it made
    elements.py          scenario -> elements; the alignment of two message sequences
  runtime/             what the traced build adds to a project
    instrument.cmake     compile every source with entry/exit hooks, link the runtime
    uml_trace.cpp        the runtime: one line per entry and exit into UML_TRACE_FILE
  docs/
    README.md            this file
    CLASS-DIAGRAMS.md    how the class-diagram flow reads, extracts and compares
    STATE-DIAGRAMS.md    the same for state machines
    SEQUENCE-DIAGRAMS.md the same for sequence diagrams
    UML-CPP-MAPPING.md   the rules that turn UML into C++ and back
```

## Running

```bash
python3 tools/verify.py                  # asks which project; Enter repeats the last choice
python3 tools/verify.py project          # one project, by name or path
python3 tools/verify.py --all            # every project
```

The projects are `project/` (the student's own) and every folder under `examples/`. Designs are
the files in a project's `diagrams/input/`. Each run empties that project's `diagrams/output/`
and removes its `reports/*-report.md` first, so nothing stale survives.

A project that is not far enough yet is skipped, not failed: with no design it says where to save
one; with a design but no implementation it still converts the design to mermaid (a flow raises
`NotReady`). The exit status is 1 only when a report could not be made — for example, the
implementation does not build; the compiler's errors are printed so VS Code can link them.

## Adding a diagram type

A flow is a subpackage of `umlverify` with three names:

| Name | What |
|---|---|
| `NAME` | the input file name it handles, without `.drawio` — e.g. `"sequence"` |
| `FILE` | that name as shown to people — `"sequence.drawio"`, or `"state-<class>.drawio"` |
| `SUBJECT` | optional: set it when the file name carries a subject after a dash, as `state-door.drawio` does; `ctx.subject` is then `"door"` |
| `TITLE` | a human-readable name — e.g. `"Sequence diagram"` |
| `run(ctx)` | reads `ctx.input`, writes `ctx.output("…")` and `ctx.report`, returns a `core.compare.Result`; raises `core.project.FlowFailed` with a plain-language reason when it cannot |

Then add it to `FLOWS` in `__init__.py`. Everything shared is in `core/`: reading draw.io pages
and edge routing (`core.drawio`), parsing headers with libclang (`core.cpp`), the comparison
(`core.compare.compare` — you supply the elements and their categories), the report
(`core.report.render` — you supply the wording in a `ReportText`), the colour palette, status
marks and legend for the comparison drawing, and the CMake build gate. `class_diagram/` is the
reference for how the pieces fit; `state_diagram/` is a second, smaller instance of the same
shape.

## Design decisions

| Decision | Why |
|---|---|
| The implemented design is extracted from the code, never by an AI | Exact and repeatable. An AI reading the code tends to report the design it has already seen instead of the code. |
| Deterministic comparison, no weights | Same inputs, same report, nothing to argue with; a missing class outweighs a missing attribute only because its members go missing with it. |
| The report never fails a build | It is for self-assessment and instructor visibility, not a grade gate. |
| No layout engine | The comparison reuses the positions from the person's own draw.io file; the AI's additional classes go in a column on the right. |
| A state machine is read from a table, never from `handle()`'s body | A method body can be written a hundred ways; a table has one shape, so libclang reads it back exactly. The table is the design, `handle()` only runs it. |
| A sequence diagram is recorded from a run, never inferred from the code | The calls a scenario makes are exactly what the diagram shows, and a deterministic run shows them exactly. Compiler instrumentation records them, so the implementation needs no trace calls and cannot forget or fake one. |
| Unreadable parts of a design are warnings, never silent drops | A silently dropped element would look exactly like an implementation mistake. |

## Requirements and platform notes

Python 3, CMake, a C++20 compiler, and the libclang Python bindings (`requirements.txt`; the
VS Code task *Set up Python environment* installs them into `.venv/`). Sequence diagrams also
need `nm` (part of every toolchain) and a compiler that supports `-finstrument-functions`
(clang and GCC do).

libclang must match the standard library headers it parses. On macOS the `libclang` wheel's
bundled LLVM fails on Apple's libc++ (`'_Tp' does not refer to a value`), so `cpp_extract.py` uses
the Command Line Tools' `libclang.dylib` and passes the SDK path with `-isysroot`. On Linux the
system libclang matches. Windows is untested.

## The examples are the test suite

`examples/1-class-simple`, `examples/3-state-simple` and `examples/5-sequence-simple` must
score 100 %, and `examples/2-class-library`, `examples/4-state-order` and
`examples/6-sequence-library` must give exactly the differences their READMEs describe. After changing the library, run `tools/verify.py --all` and check
`git diff examples/`: generated files should only change when you meant them to.

Also look at what the library draws. `node tools/render-drawio/render.js <file.drawio>` renders
every page to PNG with draw.io's own viewer (set up once with
`npm install --prefix tools/render-drawio`). The checklist, and draw.io quirks found this way,
are in `.claude/skills/drawio-visual-check/SKILL.md`.

The draw.io reader was checked against a design with known content (every one of its 70 facts
reproduced), and the libclang extractor once found a relation missing from a hand-written
"expected" diagram — which is why expected diagrams are never written by hand.
