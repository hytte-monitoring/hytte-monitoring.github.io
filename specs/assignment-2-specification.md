# Assignment 2 – Specification

Step 2 of the spec-driven AI flow. This is the instruction set for any AI agent
that implements assignment 2. It builds on the exploration in
[research/assignment-2-input-set-exploration.md](../research/assignment-2-input-set-exploration.md),
and the plan is in
[plans/assignment-2-implementation-plan.md](../plans/assignment-2-implementation-plan.md).

Status: hardware choices in §3 are a **proposal awaiting team approval**
(Team Guide §19).

## 1. Ground truth and deviations (non-negotiable)

- The input set is the UML diagrams in `model/` and the ADRs in `model/adr/`.
  The AI **must not deviate** from it, and **must not edit** it.
- When the input set is unclear, use `model/Team_Guide.md` as the fallback.
  If that does not settle it, make the smallest assumption.
- **Every** such case is a deviation. Log it in
  `project/reports/deviations.md` (ID, unclear element, resolution, source)
  at the moment it is made, and report it to the user. Do not mark an AI
  assumption as resolved; the team decides.
- No new features. The IoT parts (§3–§5) demonstrate behaviour the model
  already has.
- Full rules: [CLAUDE.md](../CLAUDE.md) and [AGENTS.md](../AGENTS.md).

## 2. Output targets

| Target | Location | Built from |
|--------|----------|------------|
| Model implementation (C++20, host) | `project/impl/` | The verifier inputs in `project/diagrams/input/` (generated from `project/diagrams/conversion/`) |
| micro:bit firmware | `firmware/` | `project/impl/include` and `src` **unchanged**, plus an I/O layer |
| Dashboard and database | `website/dashboard/` | Serial protocol §5, database §6. Runs in each visitor's browser, with no server; offers the firmware `.hex` for download |
| Reports | `project/reports/` | Verifier reports, `fom.csv`, `deviations.md`, `tests-and-benchmarks.md`, `quality-review.md` |

## 3. Hardware (proposal)

- Board: BBC micro:bit v2.
- Sensor: buttons A and B, and the accelerometer (shake).
- Actuator: the 5x5 LED matrix. The speaker is optional.

| Board input | Model event | Model reference |
|-------------|-------------|-----------------|
| Button A | DoorSensor detects the door opened | Class diagram `DoorSensor`. Team Guide §6: in AWAY this creates a Warning |
| Shake | SmokeSensor detects smoke, a Critical Incident | Sequence `smoke_escalation`. ADR-001 |
| Button B | The owner resolves the active Incident | State machine `ownerResolved`. Team Guide §8 |
| Buttons A+B | The owner changes mode HOME ⇄ AWAY | `Cabin.changeMode()`. Team Guide §6 |

| Model state | LED matrix |
|-------------|------------|
| HOME, no active Incident | `H` |
| AWAY, no active Incident | `A` |
| Incident in `Warning` | blinking `!` |
| Incident in `Critical` | flashing full matrix |
| Incident moves to `Closed` | tick, then the mode letter |

## 4. Structure (single responsibility)

```
project/impl/include/hytte/   one header per model class (verified)
project/impl/src/              one source per class
project/impl/scenarios/        one program per sequence diagram
project/impl/tests/            unit tests (not compared by the verifier)
firmware/src/main.cpp          wiring only, no logic
firmware/src/io/input_driver   buttons and accelerometer → model events
firmware/src/io/output_driver  model state → LED matrix
firmware/src/io/serial_link    model events → serial lines (§5)
website/dashboard/             index.html, serial.js, db.js, app.js, style.css
```

The firmware may not change the model classes. If the model is not enough
to run on the board, that is a deviation, and the team decides.

## 5. Serial protocol (board → dashboard)

- 115200 baud. One JSON object per line, ending with `\n`.
- `{"type":"event","sensor":"door","mode":"AWAY"}`
- `{"type":"incident","id":"I-3","severity":"WARNING","state":"Warning"}`
- `{"type":"incident","id":"I-3","severity":"CRITICAL","state":"Critical"}`
  (upgrade, same `id`, Team Guide §7)
- `{"type":"incident","id":"I-3","state":"Closed"}`
- `{"type":"mode","mode":"HOME"}`

## 6. Database

- IndexedDB through Dexie.js, in the browser, as in the course template.
- Table `sessions`: one row per board start (`hello`).
- Table `events`: every line from the board, append only.
- Table `incidents`: **one row per Incident, updated in place**. This is
  the Incident/Event History (Team Guide §9). The key is `session/id`,
  because the board restarts its ids at `I-1` after a reset.
- Export and import as JSON, plus clear.
- The board keeps only the latest 20 Incidents (F13). The database is where
  the full history lives.
- **Later option:** DoltHub as the long-term backend (research Q7). Keep the
  `events` and `incidents` tables flat, with plain columns, so they can be
  imported into SQL tables without changes.

## 7. Verification (required before any phase is called done)

1. **Alignment:** run `.venv/bin/python tools/verify.py project`. Target:
   100 % on every report, or every remaining difference explained by a
   logged deviation.
2. **Unit tests** (`project/impl/tests/`, run with CTest). All must pass:
   - ADR-001: smoke and connection monitoring cannot be disabled; Critical
     thresholds are not user-controlled.
   - Team Guide §7: Warning → Critical upgrades the **same** Incident.
   - Incident state machine: every transition in `state-incident`.
   - Team Guide §6: door events create no Incident in HOME, and do in AWAY.
3. **Benchmarks:** host time per `evaluateEvent()` and per
   `Incident::handle()`; firmware flash and RAM size; on the board, the time
   from a button press to the LED change.
4. **Figure of Merit:** after each iteration, add a row to
   `project/reports/fom.csv` with the alignment per diagram, tests passed and
   the deviation count. At least 3 points, starting from the baseline.
5. **Failures:** report every failing test, every alignment below 100 % and
   every new deviation. Never hide one.

## 8. Quality report (after implementation)

When the implementation is done, the AI writes `project/reports/quality-review.md`:

- Readability, judged for a junior software engineer.
- Documentation coverage.
- Structure and SRP.
- Test coverage and results.
- Benchmark results.
- Alignment scores.
- Open deviations.

Judge it against common industry standards and list concrete weaknesses.
