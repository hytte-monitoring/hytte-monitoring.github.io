# Assignment 2 – Input Set Exploration

Step 1 of the spec-driven AI flow (assignment 1): explore the input set, and list
everything that is unclear, ambiguous, missing, or needs an assumption before a
high-quality implementation can be built. That means one that is maintainable,
well documented, fully tested, professionally structured and performant.

The intention is to extend the Hytte Monitoring mock-up into a tiny IoT system:
the model runs on a micro:bit, events are stored in a database, and a WebSerial
dashboard shows them. The input set in `model/` is the ground truth.

Next step: [specs/assignment-2-specification.md](../specs/assignment-2-specification.md).

## 1. The input set

| Element | File | Verifiable by `tools/verify.py` |
|---------|------|---------------------------------|
| Class diagram | `model/class-diagram/class-diagram.drawio` | Yes, after conversion |
| State machine diagram (2 pages: *System Operation*, *Incident Lifecycle*) | `model/statemachine-diagram/statemachine-diagram.drawio` | Partly. A flat machine per class only |
| Sequence diagram | `model/sequence-diagram/sequence-diagram.drawio` | Partly. One path, method calls only |
| Use case diagram | `model/use-case-diagram/use-case-diagram.drawio` | No (documentation) |
| Activity diagram | `model/activity-diagram/activity-diagram.drawio` | No (documentation) |
| ADR-001 Safety-critical monitoring cannot be disabled | `model/adr/ADR-001-...md` | Through unit tests |
| ADR-002 Resilient monitoring | `model/adr/ADR-002-...md` | Through unit tests (simulated) |
| **Fallback:** Team Guide | `model/Team_Guide.md` | Not input. Used only when the UML and ADRs are unclear |

Resolution order, recorded in [CLAUDE.md](../CLAUDE.md): UML and ADRs first, then
the Team Guide, then an AI assumption. Every use of the Team Guide or an
assumption is a **deviation**, logged in
[project/reports/deviations.md](../project/reports/deviations.md) and counted in
the Figure of Merit.

## 2. What assignment 2 adds on top of the input set

| Area | Requirement | Covered by the input set? |
|------|-------------|---------------------------|
| System | 1 sensor and 1 actuator on a microcontroller | No. Hardware is new; the model only has simulated sensors |
| System | The assignment 1 code runs on the microcontroller | Partly. The assignment 1 code is the C++ in `project/impl/`, generated from the model |
| Verification | Unit tests and benchmarks | No. ADR-001 rules are testable |
| Verification | Automated model extraction and deterministic verification | Yes, with `tools/verify.py` from the course template |
| Verification | A Figure of Merit with at least 3 points, starting from a baseline | No. Defined in the spec |
| Control | Models as executable program; SRP folders and files | Partly. `AGENTS.md` maps UML to C++ |
| Understanding | A database filled from the microcontroller | Partly. Incident/Event History (Team Guide §9) is the natural database |
| Understanding | A WebSerial dashboard showing the database | Partly. The use case diagram has *View Monitoring Dashboard* and *View History* |
| Understanding | 5 slides, a 30-second video, a demo | No. Plan phase 7 |

## 3. Findings: unclear, ambiguous or missing in the input set

### 3.1 Resolved through the Team Guide or an assumption

All of these are logged with their resolution in `deviations.md`:

| ID | Finding |
|----|---------|
| D01 | The class diagram lines have no arrowheads, so navigability is unclear |
| D02 | No role names on associations |
| D03, D04 | Missing multiplicities (Owner–Contact, Owner–Incident, System–Cabin) |
| D05 | `DateTime` type undefined |
| D06 | `<<abstract>>` Sensor without an abstract method |
| D07, D08, D10 | Behaviour of `changeMode()`, `monitor()` and `evaluateEvent()` not specified |
| D09 | The state machine guard *contacts configured*, but Incident has no link to contacts |
| D11 | Sequence lifelines (Communication Service, Emergency Service) are not classes |
| D12 | Sequence messages are prose, not methods |
| D13 | History messages are drawn as self-messages, but the methods are on `IncidentHistory` |
| D14 | The sequence calls classes that MonitoringSystem has no relation to |
| D15 | The owner notification has no receiving method on `HytteOwner` |

### 3.2 Inconsistencies between diagrams (team decision needed)

1. **Sequence vs class diagram:** MonitoringSystem must reach IncidentHistory
   and EmergencyContact (D14). Either add the relations to the class diagram,
   or change the sequence.
2. **State machine vs class diagram:** the Incident state machine needs
   `state`, `handle()`, and the guard and action methods. The class diagram
   does not show them.
3. **Class diagram:** `Incident ..> EmergencyContact` is drawn, but no
   Incident method uses EmergencyContact, so the code cannot express it.
4. **Class diagram:** the sensor subclasses do not show the
   `detectCondition()` they must override (side effect of D06).

### 3.3 Limits of the verifier (not deviations, recorded in the conversion README)

- It does not read plain rectangles with HTML text as classes, so the
  diagrams are converted (`project/diagrams/conversion/`).
- It does not support concurrent regions, `entry` / `exit` actions,
  guarded initial transitions, `alt` / `opt` fragments, or prose messages.
- It cannot verify use case and activity diagrams.

### 3.4 Open questions for assignment 2 (not answerable from the input set)

| # | Question | Proposed answer (spec) |
|---|----------|------------------------|
| Q1 | Which board? | micro:bit v2: buttons, accelerometer, LED matrix and speaker are built in. It is connected and works (`/dev/ttyACM0`) |
| Q2 | Which simulated sensors do the board inputs stand for? | Button A = DoorSensor, shake = SmokeSensor, button B = owner resolves, A+B = HOME/AWAY |
| Q3 | What goes into the database? | Incident/Event History records (one per Incident, updated in place, §9) and raw events |
| Q4 | How do the C++ model classes run on the micro:bit? | The firmware compiles `project/impl/` unchanged and adds a thin I/O layer |
| Q5 | Which Figure of Merit? | Verifier alignment % per diagram, plus the deviation count |
| Q6 | Should the guidance steps (Suggested Next Steps) appear on the board? | No. Dashboard only (UI) |

## 4. Quality considerations

| Quality | What it means here | How it is checked |
|---------|--------------------|-------------------|
| Maintainable | The model is the source; code is regenerated or fixed against it | The verifier on every change |
| Documented | Every class file, deviation, decision and step is written down | `deviations.md`, `WORKFLOW.md`, conversion README |
| Tested | ADR-001 rules, the Warning → Critical upgrade on the same Incident, resolve | Unit tests (spec §6) |
| Structured | One class per file; domain separate from I/O; folders by responsibility | Spec §4, `AGENTS.md` |
| Performant | Event to LED reaction is fast enough to feel instant; the firmware fits the board | Benchmarks (spec §6) |

## 5. Reference: course template (aiunderstand/ModelDrivenDesign_ex2)

- Repo: https://github.com/aiunderstand/ModelDrivenDesign_ex2 (copied at commit
  `d439b1a`, see README Credits)
- Demo: https://aiunderstand.github.io/ModelDrivenDesign_ex2/microbit/
- **Pipeline:** a person draws class, state and sequence diagrams in draw.io.
  The AI implements them in C++ following `AGENTS.md`. `verify.py` extracts
  the implemented design (libclang for classes and states, a traced run for
  sequences) and reports an alignment score and a colour-coded comparison.
  It is deterministic.
- **micro:bit demo:** tilt and buttons as input, the board shows the state,
  WebSerial in Chrome or Edge, and IndexedDB through Dexie.js as the
  database.
