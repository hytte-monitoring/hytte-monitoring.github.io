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

**Result: 3/3 suites, 70/70 checks passed** (FoM point 10; earlier points had 27, 51, 55, 63 and 67). The tests now read id and severity through the model's getters (F16), not `TestAccess`.

| Suite | What it checks | Model source | Checks |
|-------|----------------|--------------|-------:|
| `test_incident` | Starts in `New`, status Active | State machine initial state | 2 |
| | `New → Warning`, `New → Critical` | State machine | 3 |
| | Warning → Critical upgrades the **same** Incident: id unchanged, still Active | State machine, Team Guide §7 | 4 |
| | `ownerResolved` closes from Warning and from Critical | State machine, Team Guide §8 | 4 |
| | Escalation events keep a Critical Incident Critical | State machine | 3 |
| | A Warning ignores Emergency Service escalation | State machine (no arrow), Team Guide §11 | 4 |
| | Events with no arrow are ignored, including every event after `Closed` | State machine | 3 |
| | The guard `contactsConfigured` is true only while a contact exists | State machine guard, Team Guide §10 (team decision on D09) | 3 |
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

**On-board latency** (model update and LED redraw). The board measures it
itself with `system_timer_current_time_us()` and sends it as a `latency`
line. Recorded during the Gate 4 tests, with the raw logs in
[`board-logs/`](board-logs/):

| Input | Measurements | Median |
|-------|--------------|-------:|
| Door, button A, in HOME (no Incident) | 255, 240 µs | ~248 µs |
| Door, button A, in AWAY (a Warning Incident is created) | 319, 326, 442, 407, 415 µs (and 91 µs, see below) | 407 µs |
| Smoke, shake (a Critical Incident is created, the contact notified) | 303, 295, 331, 352, 322, 396, 413 µs | 331 µs |
| Resolve, button B | 53, 51, 56, 48, 59, 62, 65, 68, 45, 71, 70 µs | 59 µs |

**The latency grows as the history fills.**
- Door in AWAY went 319 → 415 µs, and smoke 303 → 413 µs, while the
  history grew from about 10 to 20 Incidents.
- Cause, in the board code: every LED redraw (4 times a second, and on
  every event) calls `viewHistory()`, which **copies every Incident**,
  strings included, to find the newest active one.
- **Improvement for later:** ask the history only for the newest active
  Incident instead of copying all of them.
- The one outlier, **91 µs**, came when the door was pressed while the
  previous resolve's tick was still on screen. The redraw was skipped, so
  most of every measurement is the LED redraw, not the model.

All are well under 1 ms. The button debounce and the 250 ms blink cycle,
not the model, decide how fast it feels.

## Board test (Gate 4, run 1)

| Step | Board output | Result |
|------|--------------|--------|
| Shake ×2 in HOME | Critical `I-10`, `I-11` | ✅ smoke is Critical in any mode (ADR-001) |
| A+B ×2 | `AWAY`, `HOME` | ✅ |
| A in HOME | `event door`, no Incident | ✅ Team Guide §6 |
| Shake ×2 | Critical `I-12`, `I-13` | ✅ |
| B ×2 | `I-13` Closed, then `I-12` Closed, same ids | ✅ newest active first; same record updated (§8, §9) |
| A in HOME, A+B | no Incident, `AWAY` | ✅ |

Ids started at `I-10`, because 9 Incidents were made before the capture:
ids are never reused (D21). **Not covered in run 1:** a door in AWAY → a
Warning (the blinking `!`).

## Board test (Gate 4, run 2)

| Step | Board output | Result |
|------|--------------|--------|
| (unintended) | smoke → Critical `I-14` | ⚠️ the shake gesture fired while the board was handled to press B. A weakness of the hardware mapping (spec §3), not the model |
| B ×2 | `I-14` Closed, `I-11` Closed | ✅ newest active first |
| A in AWAY | Warning `I-15` | ✅ **the Warning path**, Team Guide §6 |
| B | `I-15` Closed | ✅ same id, severity WARNING kept |
| A in AWAY | Warning `I-16` | ✅ |
| B, then A, B, shake, B, B | `I-16` Closed, Warning `I-17` and Closed, Critical `I-18` and Closed, then `I-10` Closed | ✅ every old Incident resolved, newest first |
| A, B, A, B, A, shake | Warnings `I-19`, `I-20` (both closed), Warning `I-21`, Critical `I-22` | ✅ |

**History limit used on the board:** 22 Incidents were created in total, so
the limit of 20 (F13) dropped old ones, with no errors.

**Gate 4 result:** every input gives exactly what the model describes, in
both modes. Still active at the end: `I-21` (Warning) and `I-22`
(Critical). The LED patterns are confirmed by the team, because the serial
log does not show the display. Not testable on the board: Warning →
Critical on the same Incident, because no input maps to `conditionWorsens`
(it is covered by the unit tests).


## Board test (Gate 4, run 3, after the LED fix)

**What the user saw:** during run 2 the board showed `!` and never `A`.

**Cause, in the board code:**
- The LEDs showed the *newest* active Incident.
- The old Critical `I-10` stayed active behind each newer Warning, so a
  Critical was **hidden** behind a Warning.
- There was almost always some Incident active, so `A` (no active Incident)
  rarely had a chance to appear.

**Fix (firmware only, no model change):**
- The LEDs show the **most serious** active Incident: Critical before
  Warning.
- The board sends a `display` line whenever the LED pattern changes, so the
  log proves what the LEDs showed.
- The line is sent by the redraw loop, not by the input handler, so it does
  not add to the measured latency.

**Run 3** ([log](board-logs/2026-10-27-gate4-run3.jsonl), 91 lines). The
user's test sequence appears twice, and both times it is correct:

| Step | Log | Result |
|------|-----|--------|
| A+B, twice | `mode HOME`, display `H`, then `mode AWAY`, display `A` | ✅ from `?` the first press goes HOME (the rule: from HOME go AWAY, otherwise HOME) |
| A | Warning `I-1`, display `warning` | ✅ |
| Shake | Critical `I-2`, display `critical` | ✅ the Critical wins over the Warning |
| B | `I-2` Closed, `tick`, `warning` | ✅ the Warning is still active |
| B | `I-1` Closed, `tick`, `A` | ✅ `A` stays |

- The board restarted 3 times during the capture (3 `hello` lines, and the
  ids start again at `I-1`). This is to be confirmed by the user, probably
  the reset button.
- B with nothing active sends `no active Incident to resolve`.
- **The user confirmed that the LEDs matched at every step.** The only
  difference from the AI's instruction table was A+B: from `?` the board
  shows `H` first, then `A`. The board was right and the table was wrong
  (it left out the HOME step). Starting in HOME is a design choice, because
  Team Guide §6 only says the owner chooses at startup.

**Latency in run 3** (0–3 Incidents on the board):

| Input | Measurements |
|-------|--------------|
| Door | 27–146 µs |
| Smoke | 66–112 µs |
| Resolve | 28–133 µs |

The first resolve after a restart (133, 122 µs) includes building the tick
image once.

Compared with runs 1 and 2 (10–22 Incidents, 240–442 µs), this **confirms
the performance finding**: the cost is the board code copying the whole
history on every redraw, not the model. A door in HOME took 248 µs with
about 10 Incidents stored, and 27 µs with none.

## Dashboard test (Gate 5)

- **Browser:** Mozilla's Firefox 159.0 (WebSerial since 151), in a separate
  profile. Ubuntu's snap Firefox and VS Code's preview cannot reach the
  serial port.
- **Result, reported by the user:** the dashboard connected to the
  micro:bit and worked.
- **Stored data:** read straight from Firefox's IndexedDB SQLite file in the
  profile (`storage/default/http+++localhost+8000/idb/`):

| Table | Rows |
|-------|-----:|
| sessions | 1 |
| incidents | 5 (`1/I-1` … `1/I-5`) |
| events | 39 |

- 5 Incidents are stored in 5 rows, so the resolves updated the existing
  rows instead of adding new ones: one record per Incident (Team Guide §9).
- The copy was taken while Firefox was running, so the very latest writes
  may be missing from it. The result is not affected.
