# 5 · Thermostat

The smallest sequence diagram: one scenario over three classes, implemented exactly as
designed.

**Result: 100 % alignment** — all 7 elements of the scenario identical (4 lifelines, 3
messages), and the 13 elements of the class diagram too.

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `5-sequence-simple`, then open
[`reports/sequence-set_target-report.md`](reports/sequence-set_target-report.md) and
[`reports/class-report.md`](reports/class-report.md).

## The design

| Drawing | Shows |
|---|---|
| [`diagrams/input/class.drawio`](diagrams/input/class.drawio) | `Thermostat`, which refers to a `Sensor` and a `Heater` |
| [`diagrams/input/sequence-set_target.drawio`](diagrams/input/sequence-set_target.drawio) | the scenario *set target*: the user sets 21 °C, the thermostat reads the sensor (18.5), and turns the heater on |

## How a scenario is verified

A sequence diagram is not read from the code; it is **recorded** from a run.
[`scenarios/set_target.cpp`](impl/scenarios/set_target.cpp) is a small program:

- `main()` creates the sensor, the heater and the thermostat. That set-up is not in the
  diagram and is not recorded.
- `scenario()` does what the actor does in the drawing: `thermostat.setTarget(21.0)`.

The verifier builds the implementation a second time with every function instrumented, runs
the program, and writes down each call between the project's classes as it happens:
`Thermostat::setTarget` from outside any class (the actor), then `Sensor::read` and
`Heater::turnOn` from inside it. Those calls, in order, are
[`diagrams/output/sequence-set_target-implemented.mmd`](diagrams/output/sequence-set_target-implemented.mmd),
and they are compared with the drawn messages. The implementation contains no tracing code;
the return arrow `18.5` is documentation and is not compared.

`CMakeLists.txt` builds the scenario like any other executable:
`add_executable(scenario_set_target scenarios/set_target.cpp)`, linked to the library. That
is the whole contract; see
[UML-CPP-MAPPING.md](../../tools/umlverify/docs/UML-CPP-MAPPING.md#sequence-diagrams).

## Try this

Break the implementation on purpose in [`thermostat.cpp`](impl/src/thermostat.cpp), run the
task again, and watch `reports/sequence-set_target-report.md` and its comparison change:

| Edit in `setTarget()` | Result |
|---|---|
| call `heater_.turnOn()` before `sensor_.read()` (and drop the later call) | ✏️ changed: `read()` now follows `turnOn()` instead of `setTarget()`, amber — 85.7 % |
| add `if (heater_.isOn()) return;` after reading the sensor | ➕ extra message `Thermostat → Heater : isOn()`, green — 87.5 % |
| make the condition always false, so `turnOff()` runs instead of `turnOn()` | ➖ missing `turnOn()` and ➕ extra `turnOff()` — 75.0 % |

Then undo your changes (`git checkout examples/5-sequence-simple`) to get back to 100 %.

## Files

```
diagrams/input/class.drawio                 the class diagram                        ← input
diagrams/input/sequence-set_target.drawio   the scenario "set target"                ← input
impl/include/climate/*.hpp                  the implementation's headers (compared)  ← input
impl/src/*.cpp                              the implementation's sources (built, not compared)
impl/scenarios/set_target.cpp               the scenario program (built, run, recorded)
diagrams/output/                            generated: <design>-design.mmd, <design>-implemented.mmd,
                                                       <design>-comparison.drawio
reports/<design>-report.md                  generated: the reports, one per design file
build-trace/                                the traced build and the recorded trace (not committed)
```
