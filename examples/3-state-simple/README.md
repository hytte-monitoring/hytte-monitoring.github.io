# 3 · Door

The smallest state machine: one class, three states, four events, implemented exactly as
designed.

**Result: 100 % alignment** — all 12 elements of the state machine identical, and the 4
elements of the class diagram too.

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `3-state-simple`, then open
[`reports/state-door-report.md`](reports/state-door-report.md) and
[`reports/class-report.md`](reports/class-report.md).

## The design

Two drawings share one implementation:

| Drawing | Shows |
|---|---|
| [`diagrams/input/class.drawio`](diagrams/input/class.drawio) | the class `Door`: a `state` attribute, `handle(event)` and `state()` |
| [`diagrams/input/state-door.drawio`](diagrams/input/state-door.drawio) | its state machine: `Closed`, `Open` and `Locked`; initial state `Closed`; events `open`, `close`, `lock` and `unlock` |

A door can only be locked while it is closed, so `lock` in `Open` does nothing: there is no
arrow for it, and the table has no row.

## How the state machine maps to C++

Everything is in [`door.hpp`](impl/include/home/door.hpp), and it is the pattern every state
machine follows (see [UML-CPP-MAPPING.md](../../tools/umlverify/docs/UML-CPP-MAPPING.md#state-machines)):

| In the drawing | In `door.hpp` |
|---|---|
| the states | `enum class State { Closed, Open, Locked };` |
| the events | `enum class Event { open, close, lock, unlock };` |
| the arrow from the start symbol | `State state_ = State::Closed;` |
| each arrow | a row of `transitions`: `{State::Closed, Event::open, State::Open, nullptr, nullptr}` |

The last two fields of a row are the guard and the action, both member-function pointers;
this machine has none, so they are `nullptr`. [`door.cpp`](impl/src/door.cpp) holds the one
method that runs the table, `handle(Event)`, which is the same in every state machine. The
verifier reads the table and never `handle()`.

The class diagram does not repeat the machine: `State`, `Event`, `Transition` and `transitions`
belong to the state diagram and are not class-diagram elements. The class box shows only
`- state: State`, `+ handle(event: Event): void` and `+ state(): State`.

## Try this

Break the implementation on purpose, run the task again, and watch
`reports/state-door-report.md` and its colour-coded comparison change:

| Edit in `door.hpp` | Result |
|---|---|
| in the `unlock` row, change the target to `State::Open` | ✏️ changed transition `Locked on unlock`, amber — 91.7 % |
| delete the `close` row | ➖ missing transition `Open on close` and missing event `close`, red — 83.3 % |
| add a row `{State::Open, Event::lock, State::Locked, nullptr, nullptr}` | ➕ extra transition `Open on lock`, green — 92.3 % |
| initialise `state_` with `State::Open` | ✏️ changed initial transition `[*] -->`, amber — 91.7 % |
| add `Broken` to `State` | ➕ extra state `Broken`, green in the column on the right — 92.3 % |

Then undo your changes (`git checkout examples/3-state-simple`) to get back to 100 %.

## Files

```
diagrams/input/class.drawio        the class diagram                         ← input
diagrams/input/state-door.drawio   the state machine of Door                 ← input
impl/include/home/door.hpp         the implementation's header (compared)    ← input
impl/src/*.cpp                     the implementation's sources (built, not compared)
diagrams/output/                   generated: class-*.mmd, state-door-*.mmd,
                                              class-comparison.drawio, state-door-comparison.drawio
reports/class-report.md            generated: the reports, one per design file
reports/state-door-report.md
```
