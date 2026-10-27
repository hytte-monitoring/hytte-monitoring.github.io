# Unit tests and benchmarks (Phase 3)

How to run them (from `project/impl/`):

```
cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release && cmake --build build-release && ./build-release/benchmark
```

## Unit tests

- No test framework is needed. `tests/check.hpp` provides a `CHECK` macro,
  and CTest runs each suite.
- Incident and Cabin have a `state()` getter (F01, F04). Everything else
  is read through `tests/test_access.hpp`: Incident, Cabin and
  MonitoringSystem each declare `friend struct TestAccess;` for this. The
  verifier ignores friend declarations.

**Result: 3/3 suites, 67/67 checks passed** (FoM point 9; earlier points had 27, 51, 55 and 63). The tests now read id and severity through the model's getters (F16), not `TestAccess`.

| Suite | What it checks | Model source | Checks |
|-------|----------------|--------------|-------:|
| `test_incident` | Starts in `New`, status Active | State machine initial state | 2 |
| | `New → Warning`, `New → Critical` | State machine | 3 |
| | Warning → Critical upgrades the **same** Incident: id unchanged, still Active | State machine, Team Guide §7 | 4 |
| | `ownerResolved` closes from Warning and from Critical | State machine, Team Guide §8 | 4 |
| | Escalation events keep a Critical Incident Critical | State machine | 3 |
| | A Warning ignores Emergency Service escalation | State machine (no arrow), Team Guide §11 | 4 |
| | Events with no arrow are ignored, including every event after `Closed` | State machine | 3 |
| `test_cabin_and_sensor` | Cabin starts HOME; `changeMode()` switches HOME ⇄ AWAY | Class diagram, Team Guide §6 (D07) | 3 |
| | `monitor()` asks an enabled sensor to detect its condition | Class diagram, Team Guide §4 (D08) | 1 |
| `test_system_operation` | Cabin starts in `Awaiting`; owner chooses AWAY, then HOME, and `mode` follows | `state-cabin`, Team Guide §6 (D16) | 5 |
| | Cold weather activates protection and keeps the mode; `coldGone` deactivates it | `state-cabin`, Team Guide §4 | 6 |
| | Mode changes still work while protection is active | `state-cabin` | 3 |
| | Door and motion are ignored in HOME and handled in AWAY | `state-cabin`, Team Guide §6 (D17) | 2 |
| | ADR-002: battery on power loss, Cellular/SIM on Internet loss, both at once, and back | `state-monitoring_system`, ADR-002 | 8 |
| | A door or motion event in AWAY registers an Incident in the history; in HOME it does not | `state-cabin`, F03, F10, Team Guide §6 and §9 | 3 |
| | The `smoke_escalation` path registers one Incident, and it is Critical | Sequence `smoke_escalation`, F10, F11 | 2 |
| | A door Incident in AWAY is a Warning, read through `viewHistory()` | F11, F12 | 1 |
| | The history keeps at most 20 Incidents, drops the oldest first, and never reuses ids | F13, D21, D22 | 4 |
| | The owner resolves an Incident by its id; the others stay; an unknown id does nothing | F15, D25, Team Guide §8 | 4 |
| `test_incident` | `New → Critical` sets severity CRITICAL | State machine, F11 | 1 |

### What cannot be tested yet (findings for the team)

These rules are in the ADRs or the Team Guide, but the UML gives the code
nothing to test them with. Writing tests for them would mean inventing
behaviour, which the deviation rule does not allow.

| Rule | Why it cannot be tested |
|------|-------------------------|
| ADR-001: smoke and Internet/Connection monitoring cannot be disabled | The class diagram has no way to disable a sensor: `configureMonitoring()` has no parameters, and `enabled` has no setter |
| ADR-001: Critical thresholds are system-controlled | No class or attribute in the class diagram holds a threshold |
| The `contactsConfigured` guard | It always returns `false` (D09), so the guarded transitions cannot fire |
| Notifications (owner, contact, Emergency Service) | The methods are mock-ups with no effect to observe (Team Guide §17) |

## Benchmarks (host)

- Release build (`-O3`), g++ 13.3.0, AMD Ryzen 7 250, 1 000 000 runs per
  measurement.
- Each value is the median of 3 program runs.

| Measurement | Run 1 | Run 2 | Run 3 | Median |
|-------------|------:|------:|------:|-------:|
| Incident lifecycle: construct and 3 × `handle()` (New → Warning → Critical → Closed) | 19.3 ns | 20.0 ns | 19.4 ns | **19.4 ns** |
| `MonitoringSystem::evaluateEvent()` (the `smoke_escalation` calls, 1 contact) | 7.0 ns | 7.2 ns | 8.9 ns | **7.2 ns** |

### Re-run after F10 (FoM point 7)

- Same build and PC, but the CPU governor is `powersave`, so the PC can
  be in a slower power state.
- Median of 7 runs.
- **Only compare times measured in the same session:** the lifecycle code
  did not change, yet it now takes 45.6 ns instead of 19.4 ns.

| Measurement | Before F10 | After F10 | Ratio to the lifecycle, before → after |
|-------------|-----------:|----------:|---------------------------------------:|
| Incident lifecycle | 19.4 ns | **45.6 ns** | 1 → 1 |
| `evaluateEvent()` | 7.2 ns | **156.5 ns** | 0.37 → 3.4 |

`evaluateEvent()` became about 9 times slower relative to the lifecycle.
It now really creates an Incident and allocates it on the heap (with
`unique_ptr`, inside a growing `vector`). That is a real cost of the F10
decision. In the benchmark, 1 000 000 calls also create 1 000 000
Incidents, which shows that the history is unbounded (F13).

### Re-run after F11–F13 (FoM point 8)

- The PC was in a fast power state again (the lifecycle is back near the
  first session's value).
- Median of 5 runs.

| Measurement | Median | Ratio to the lifecycle |
|-------------|-------:|-----------------------:|
| Incident lifecycle | **22.9 ns** | 1 |
| `evaluateEvent()` | **68.2 ns** | 3.0 (was 3.4 at point 7) |

Since the history is limited to 20 Incidents, `evaluateEvent()` no longer
grows a vector of a million Incidents. It now pays for one allocation, and
for dropping the oldest Incident when the history is full.

The model's logic takes nanoseconds on the PC. On the micro:bit (64 MHz
Cortex-M4), the time from button to LED will be dominated by input
polling and the LED refresh, not the model. That, and the firmware size,
are measured in Phase 4.

## Firmware (Phase 4, micro:bit v2)

- Arm GNU toolchain 13.3.rel1, CODAL v0.3.0, codal-microbit-v2 v0.3.5,
  `-std=c++11`.
- The build has no warnings in our code. The only warning is CODAL's linker
  note about an RWX segment.

| Measure | Bytes | Note |
|---------|------:|------|
| Application code (`.text`) | 108 864 | of 512 KB flash; the SoftDevice (107 520) and bootloader (25 580) take their own space |
| Model (`hytte::` symbols) | **4 652** → **5 914** after F15/F16 | all 18 classes, 3 transition tables, the history |
| Board code (`io::` symbols) | **4 124** → **5 336** after F15/F16 | input, output and serial drivers |
| Static RAM (`.bss`) | 7 432 | of 128 KB RAM; the heap gets the rest (112 888) |

**On-board latency** (button → model → LED redraw): the board measures it
itself with `system_timer_current_time_us()` and sends it as a `latency`
line. **Pending:** someone must press the buttons. See plan Phase 4.
