# Assignment 2 – Hytte Monitoring IoT Mock-up Specification

Status: **draft, needs group agreement** (Team Guide §19).

This spec maps the ground truth in `model/Team_Guide.md` onto a
microcontroller, a database and a WebSerial dashboard. It adds no new
system features. It only chooses which existing behaviour the hardware
demonstrates.

## 1. Hardware

- Board: BBC micro:bit v2 (proposed).
- Sensor: buttons A and B (built in). The accelerometer is an optional extra.
- Actuator: 5x5 LED matrix (built in). The speaker is an optional extra.

## 2. Mapping board inputs to the conceptual system

| Board input | Simulates | Ground truth reference |
|-------------|-----------|------------------------|
| Button A | Door Sensor: door opened | §6 Door activity in AWAY creates a Warning |
| Button B | Owner marks the active Incident Resolved | §8 Resolved |
| Button A+B | Switch HOME ⇄ AWAY | §6 Monitoring modes |
| Shake (optional) | Smoke Sensor: smoke detected, Critical | §7, §12 |

Expected behaviour:

- In HOME mode, button A is logged as an event but creates no Incident.
- In AWAY mode, button A creates a **Warning** Incident with status Active.
- Shake creates a **Critical** Incident in both modes, because smoke is
  mandatory (ADR-001).
- If a Warning is active and the condition worsens, the same Incident is
  upgraded to Critical. No new Incident is created (§7).
- Button B closes the active Incident and updates its existing history
  record (§8, §9).

## 3. Board output

| State | LED matrix | Speaker (optional) |
|-------|-----------|--------------------|
| HOME, no Incident | `H` | silent |
| AWAY, no Incident | `A` | silent |
| Warning active | blinking `!` | short beep |
| Critical active | flashing full matrix | repeating alarm |
| Incident resolved | tick icon, then the mode letter | single tone |

Escalation (§10–12) is simulated as events only. No real calls or SMS are
made.

## 4. Firmware structure (one responsibility per file)

```
firmware/
  include/  src/
    Incident.*          Incident with severity, status and upgrade/resolve
    IncidentHistory.*   Registers and updates incident records
    MonitoringSystem.*  evaluateEvent / createIncident / escalateIncident
    Cabin.*             Mode (HOME/AWAY), coldProtectionActive
    sensors/*           One file per simulated sensor (Door, Smoke, ...)
    io/InputDriver.*    Buttons and accelerometer → domain events
    io/OutputDriver.*   Domain state → LED and speaker
    io/SerialLink.*     Sends and receives serial messages
    main.cpp            Wiring only, no logic
```

Class names, attributes and operations must match `model/class-diagram`
so the verifier can compare them.

## 5. Serial protocol (board ⇄ dashboard)

- Baud rate: 115200. One JSON object per line, ending with `\n`.
- Board to dashboard:
  - `{"type":"event","sensor":"door","mode":"AWAY","t":12345}`
  - `{"type":"incident","id":"I-3","severity":"WARNING","status":"Active"}`
  - `{"type":"incident","id":"I-3","severity":"CRITICAL","status":"Active"}` (upgrade, same id)
  - `{"type":"incident","id":"I-3","status":"Closed"}`
  - `{"type":"mode","mode":"HOME"}`
- Dashboard to board (optional): `{"cmd":"setMode","mode":"AWAY"}`

## 6. Database

- IndexedDB through Dexie.js, in the browser, as in the reference example.
- Tables:
  - `events`: every received event (append only).
  - `incidents`: one row per Incident, **updated in place** on upgrade,
    escalation or closing, matching Incident/Event History (§9).
- Export and import as JSON, plus clear.

## 7. Dashboard (`website/dashboard/`)

- A "Connect micro:bit" button using WebSerial (Chrome or Edge).
- Live panels: current mode, active Incident, live board state.
- History panels: event log and the Incident/Event History table from the database.
- Linked from the existing landing page.

## 8. Verification

- Inputs verified with `verify.py`: class diagram, Incident state machine,
  and one sequence scenario (Warning → upgrade → resolve).
- Unit tests (host build): HOME/AWAY door rules, Warning to Critical upgrade
  keeps the same id, resolve closes the incident and updates the same
  history record, and smoke cannot be disabled.
- Benchmark: event-to-incident latency or `evaluateEvent()` time on the host,
  plus firmware size.
- Figure of Merit: the alignment score per diagram, plotted per commit
  (see plan).

## 9. Out of scope

Everything in Team Guide §17 stays out of scope. Only one physical board is
used, and all other sensors stay simulated.
