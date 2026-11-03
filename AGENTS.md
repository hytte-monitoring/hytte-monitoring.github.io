# AGENTS.md

Instructions for AI coding agents (GitHub Copilot, Claude, Codex, …) working in this repository.

Your job is to **implement a UML design in C++**, in `project/impl/`: a class diagram and, when
the person drew them, the state machines of its classes and the sequence diagrams of its
scenarios. A person drew the design; a verifier then compares your implementation with it,
element by element, and reports every difference. Success is **100 % alignment** on every
report: the code is exactly the design, nothing more and nothing less.

## Where things are

| Path | What it is | You may |
|---|---|---|
| `project/diagrams/input/class.drawio` | the class diagram, drawn by a person | read — **never edit** |
| `project/diagrams/input/state-<class>.drawio` | the state machine of one class, drawn by a person; there may be none, one or several | read — **never edit** |
| `project/diagrams/input/sequence-<scenario>.drawio` | one scenario as a sequence diagram, drawn by a person; none, one or several | read — **never edit** |
| `project/diagrams/output/*-design.mmd` | the same designs as mermaid text, generated | read — easiest to parse |
| `project/impl/` | the implementation | **write here, and only here** |
| `project/process/` | specs and plans for your work (see below) | write |
| `project/reports/*-report.md` | the verification reports, generated, one per design file | read |
| `examples/` | worked examples | read |
| `tools/` | the verifier | read |

The `.mmd` files are created by the verifier. If they are missing, run the verifier once (see
[Check your work](#check-your-work)); it converts the drawings even before any code exists.

## Project structure

Use exactly this layout:

```
project/impl/
  CMakeLists.txt
  include/<name>/<class>.hpp    one header per class; <name> is a short lowercase project name
  src/<class>.cpp               one source per class that has code; plus src/demo.cpp
  scenarios/<scenario>.cpp      one program per sequence diagram (only if there are any)
```

- **Headers in `include/` are what gets compared with the design.** Every class, attribute,
  method and relation must be declared there. Sources in `src/` are built but not compared.
- Use `snake_case` file names (`library_item.hpp` for `LibraryItem`) and put everything in one
  namespace, e.g. `namespace library { … }`.
- `CMakeLists.txt` follows [examples/1-class-simple/impl/CMakeLists.txt](examples/1-class-simple/impl/CMakeLists.txt):
  C++20, `CMAKE_EXPORT_COMPILE_COMMANDS ON`, a static library from `src/*.cpp` with `include`
  as its public include directory, `-Wall -Wextra`, and a small `demo` executable that uses the
  classes. Each sequence diagram adds `add_executable(scenario_<scenario> scenarios/<scenario>.cpp)`
  linked to the library. The build must succeed without warnings.

## Rules for the implementation

**1. Follow the mapping exactly.** [tools/umlverify/docs/UML-CPP-MAPPING.md](tools/umlverify/docs/UML-CPP-MAPPING.md)
defines which C++ construct each UML element becomes. The verifier applies it mechanically, so
anything else is reported as a difference. The rules that matter most:

| In the design | In C++ |
|---|---|
| `Owner *-- Part` composition (filled diamond) | `std::unique_ptr<Part>` or a by-value `Part` member |
| `Owner o-- Part` aggregation (hollow diamond) | `std::shared_ptr<Part>` member |
| `A --> B` association (open arrow) | `B*`, `B&` or `std::weak_ptr<B>` member |
| `A ..> B` dependency (dashed) | `B` only in a parameter or return type, never a member |
| multiplicity `*` / `0..1` | `std::vector<…>` / `std::optional<…>` |
| `+` / `#` / `-` | `public:` / `protected:` / `private:` |
| `<<interface>>` | only pure virtual methods, no data members, virtual destructor |
| `<<abstract>>` / italic method | at least one pure virtual method (`= 0`) and data members |
| `<<enumeration>>` | `enum class` |
| underlined member (static) | `static` |

Ownership is the easy one to get wrong, because the wrong choice still compiles: do **not**
reach for `std::shared_ptr` unless the design shows a hollow diamond.

**2. Implement exactly what is drawn.**
- Every class, attribute, method and relation in the design — no fewer.
- Nothing that is not in the design: no helper or utility classes, no extra public or private
  methods, no extra data members. Put helper logic inside the method bodies in `src/`.
- Constructors, destructors and operators are fine; the diagram leaves them out by convention.
- A member that implements a relation is not also an attribute: `Playlist *-- "*" Song : songs`
  is one member, `std::vector<Song> songs_;`.

**3. Use the design's names and types.**
- Class, method and attribute names as drawn. Private data members may take a trailing
  underscore (`name_` for `name`); the verifier ignores it.
- A relation's role name is the member's name: `: borrower` → `borrower_`.
- `string` → `std::string`, `size_t` → `std::size_t`, `vector<T>` → `std::vector<T>`.
- Parameter and return types as drawn; `const T&` for class-typed parameters is fine.

**4. Implement a state machine as a transition table.** A `state-<class>.drawio` is the state
machine of that class (`state-order.drawio` → `Order`). The *State machines* section of the
mapping document defines the pattern; in short, everything lives inside the class:

| In the design | In C++ |
|---|---|
| the states | `enum class State { … }`, nested in the class |
| the events | `enum class Event { … }`, nested in the class |
| a guard `[hasKey]`, an action `/ log` | private member functions `bool hasKey() const`, `void log()` |
| each arrow | one row of `static constexpr Transition transitions[]`: `{from, event, to, guard, action}`, `nullptr` for no guard or no action, **all five fields on every row** |
| the arrow from the start symbol | the state attribute's default initializer: `State state_ = State::Closed;` |
| firing an event | `void handle(Event)`, in `src/`, walks the table; an event with no row is ignored |

The `Transition` struct and the table come after the guards and actions they name. `State`,
`Event`, `Transition` and `transitions` belong to the state diagram, not to the class diagram:
the class box shows `- state: State`, `+ handle(event: Event): void` and the guard and action
methods, nothing more. [examples/3-state-simple/impl/include/home/door.hpp](examples/3-state-simple/impl/include/home/door.hpp)
is the pattern to copy; it is the same in every state machine.

**5. Implement a sequence diagram as a scenario program, and make exactly the drawn calls.**
A `sequence-<scenario>.drawio` is verified by *running* `impl/scenarios/<scenario>.cpp` in a
traced build: every call between the project's classes is recorded, in order, and compared
with the drawn messages. The *Sequence diagrams* section of the mapping document has the
rules; in short:

- `main()` creates the objects the scenario needs (that set-up is not in the diagram), then
  calls `scenario()`. `scenario()` makes the actor's calls, and nothing else:
  `void scenario(Library& library) { library.lend("b1", "m1"); }`.
- A message `Library → Catalog : find(id)` is `Catalog::find` called from a method of
  `Library`. Make every drawn call, in the drawn order, from the drawn class, and no other
  calls between classes — a getter the diagram does not show is an extra message. A class
  calling its own private helper is fine unless the diagram draws a self-message (then it must
  happen). Return arrows are not compared; constructors are never messages.
- The scenario must be deterministic: no clock, no randomness, no input, one thread.
- Nothing to add to the code for tracing: the verifier instruments the build itself.

[examples/5-sequence-simple/impl/scenarios/set_target.cpp](examples/5-sequence-simple/impl/scenarios/set_target.cpp)
is the pattern to copy.

## Check your work

Run the verifier after every change:

- **VS Code:** Ctrl+Shift+B (Cmd+Shift+B on macOS), choose `project`.
- **Terminal:** `.venv/bin/python tools/verify.py project` (the VS Code task *Set up Python
  environment* creates `.venv/` the first time).

Then read every report in `project/reports/`: `class-report.md`, one `state-<class>-report.md`
per state machine and one `sequence-<scenario>-report.md` per scenario. Fix every **Changed**,
**Missing** and **Extra** entry and run it again until every alignment is 100 %. If a build error is reported, the compiler's
messages are printed above the summary. Do not edit the report or the files in
`project/diagrams/output/`: they are regenerated on every run.

## Process files

Keep your working notes in `project/process/`:

- `specs/` — what to build. Before writing code, write down each class from the design with its
  members and relations, each state machine with its states, events and transitions, each
  scenario with its messages in order, and the C++ construct each one maps to.
- `plans/` — how you will build it: a checklist of steps, one file per piece of work, named
  `YYYY-MM-DD-<topic>.md`.
- `plans/completed/` — move a plan here once all its steps are done and the verifier reports
  100 %.

## Examples

- [examples/1-class-simple](examples/1-class-simple/) — three classes, implemented exactly as
  designed, 100 %. **Copy its structure and style.**
- [examples/2-class-library](examples/2-class-library/) — eleven classes covering interfaces,
  abstract classes, enums, templates and every kind of relation. Its implementation contains
  **three deliberate mistakes** (listed in its README): learn from the rest, never copy those.
- [examples/3-state-simple](examples/3-state-simple/) — one class with a state machine, 100 %.
  **Copy its table pattern for every state machine.**
- [examples/4-state-order](examples/4-state-order/) — two state machines with guards, actions and
  a self-transition, next to a class diagram. Its state machines contain **three deliberate
  mistakes** (listed in its README); its class diagram is exact.
- [examples/5-sequence-simple](examples/5-sequence-simple/) — one scenario over three classes,
  100 %. **Copy its scenario program for every sequence diagram.**
- [examples/6-sequence-library](examples/6-sequence-library/) — two scenarios over five classes,
  with a self-message and a return. Its scenarios contain **three deliberate mistakes** (listed
  in its README); its class diagram is exact.

## If you change a draw.io file

This is only for work on the examples or the tools, never on `project/diagrams/input/`. Render it
and look at the result before calling it done:
`node tools/render-drawio/render.js <file.drawio>`. The checklist is the `drawio-visual-check`
skill ([.claude/skills/drawio-visual-check/SKILL.md](.claude/skills/drawio-visual-check/SKILL.md)),
which GitHub Copilot and Claude Code both load automatically; in Copilot Chat you can also type
`/drawio-visual-check`.
