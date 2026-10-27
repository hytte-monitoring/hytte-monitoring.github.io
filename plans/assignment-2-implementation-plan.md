# Assignment 2 – Implementation Plan

Step 3 of the spec-driven AI flow. This plan implements
[specs/assignment-2-specification.md](../specs/assignment-2-specification.md),
which is based on
[research/assignment-2-input-set-exploration.md](../research/assignment-2-input-set-exploration.md).

## Rules for every phase

- **Follow the spec and this plan.** Deviate only with the user's
  permission. Minor steering is given in chat; major steering goes through
  the team's models and ADRs.
- **Model alignment is critical.** It is recorded in `CLAUDE.md` (ground
  truth, deviations) and `AGENTS.md` (UML ↔ C++). Before a phase is called
  done, run the verifier and report every alignment below 100 % and every
  new deviation.
- **Two-level verification.** The verifier extracts the class diagram and
  state machines from the code (libclang), and records the sequence
  diagrams from a traced run. The generated `diagrams/output/*-implemented.mmd`
  and `*-comparison.drawio` let the team check both the code and the
  diagrams.
- **Readable for a junior software engineer.** Short functions, clear
  names, a comment where the model or a deviation explains why.
- **Commits.** Commit locally in normal-sized commits, one per logical
  change. Only the team pushes.
- **Documentation.** `WORKFLOW.md` gets a step and the prompt for every
  piece of work.
- **Agents.** One agent works at a time on this repo. If parallel agents
  are used, they must tell each other before building, running the
  verifier, or editing the same files. When splitting work, a stronger model
  plans and orchestrates, and a cheaper model implements.

## 👁 Human gate (after every phase)

The team checks before the next phase starts:

1. **Read the commits**, not only the AI's summary.
2. Open the comparison drawings in `project/diagrams/output/` and the
   reports in `project/reports/`.
3. Go through new rows in `deviations.md`. Accept or reject each AI
   assumption, and change the models by hand if needed.
4. For hardware phases, try it on the board yourself.
5. Approve in chat, or loop back.

---

## Phase 0 – Setup ✅

- [x] Folder structure: `project/`, `firmware/`, `website/dashboard/`.
- [x] Copy the verifier, examples, `AGENTS.md` and VS Code tasks from the
      course template, with credit.
- [x] Python `.venv` with libclang, and clang installed.
- [x] `CLAUDE.md` with the ground truth and deviation rules.
- [ ] Team agrees on the hardware proposal (spec §3).

👁 **Gate 0:** the toolchain verifies `examples/1-class-simple` at 100 % ✅.
The hardware proposal is still open.

## Phase 1 – Baseline (FoM point 1) ✅

- [x] Convert the class diagram and the Incident state machine to the
      verifier's format (`project/diagrams/conversion/`). Notation only; the
      rest is logged as deviations.
- [x] First AI implementation from the converted diagrams only.
- [x] Verify and commit the reports unfixed: class 73.6 %, state 100 %.
- [x] Start `fom.csv` and `deviations.md`.

👁 **Gate 1:** the team reviews `conversion/README.md` and `deviations.md`
D01–D10. **Open.**

## Phase 2 – Close the gap (FoM points 2, 3, …) – in progress

- [x] Convert one sequence path, `smoke_escalation`, and implement its
      scenario. Sequence 100 %; class regressed to 72.3 % (D14). Point 2.
- [x] Implement to-many associations as `vector<weak_ptr<T>>`. Class
      83.8 %. Point 3.
- [x] Convert the System Operation page (`state-cabin`,
      `state-monitoring_system`, both 100 %) and add `state()` getters to
      Incident and Cabin (F01, F02, F04). Class 76.3 %, tests 51/51. Point 5.
- [x] Add the association Cabin → MonitoringSystem (F03). Class 76.5 %. Point 6.
- [x] IncidentHistory owns the Incidents, a composition (F10). Class 76.5 %, tests
      55/55. Point 7.
- [x] Decided and done: F11 (severity parameter), F12 (`viewHistory()` returns
      the Incidents), F13 (history limit 20). Class 76.7 %, sequence 83.3 %
      (F14), tests 63/63. Point 8.
- [ ] F14: the team decides how the sequence diagram shows the severity call.
- [ ] **Team decisions on the models** (see the research §3.2), then
      re-convert and re-verify:
  - add the Incident state machine members to the class diagram;
  - add MonitoringSystem → IncidentHistory and EmergencyContact, or change
    the sequence (D14);
  - the `Incident ..> EmergencyContact` dependency;
  - the sensor subclasses' `detectCondition()` (D06).
- [ ] One verifier run and one `fom.csv` row per iteration.

👁 **Gate 2:** every remaining difference is explained by a deviation the
team accepted.

## Phase 3 – Unit tests and benchmarks ✅ (Gate 3 open)

- [x] `project/impl/tests/` with CTest: 2 suites, 27/27 checks pass. They
      cover every Incident transition, the same-Incident upgrade, resolve,
      Warning not escalating to the Emergency Service, and Cabin mode
      switching.
- [x] Host benchmarks in `project/impl/benchmarks/`. Results and untestable
      rules in `project/reports/tests-and-benchmarks.md`.
- [x] `tests_passed` recorded in `fom.csv` (point 4).
- [ ] ADR-001, the HOME/AWAY door rule and ADR-002 are **not testable**
      with the current model. The team decides what to add to the model
      (see the report).

👁 **Gate 3:** the team runs the tests themselves (`ctest`) and checks
that they test the model, not the implementation's own guesses.

## Phase 4 – Firmware on the micro:bit

**Prerequisites (checked 2026-10-27, WORKFLOW Step 19):**

| Need | Status |
|------|--------|
| micro:bit v2 on USB | ✅ DAPLink v0257, ID starts `9906` (V2), drive `/media/mar/MICROBIT`, serial `/dev/ttyACM0` |
| Serial port access | ✅ the user is in the `dialout` group |
| git, python3, cmake, make, curl | ✅ |
| ninja | ❌ optional: CODAL falls back to make (`sudo apt install ninja-build` makes builds faster) |
| Arm GNU toolchain (`arm-none-eabi-gcc`) | ❌ the template's `build.sh` downloads 13.3.rel1 (~130 MB) into `firmware/.build/`; no sudo needed |
| CODAL (microbit-v2-samples v0.3.0, codal-microbit-v2 v0.3.5) | ❌ cloned and fetched from GitHub on the first build |
| C++11 compatibility (CODAL compiles with `-std=c++11`) | ⚠️ tested with `g++ -std=c++11 -fno-exceptions -fno-rtti`: everything compiles, but linking fails on `Incident::transitions`. Fix: one out-of-class definition in `src/incident.cpp` (src only, not compared by the verifier) |
| Chrome or Edge for WebSerial (Phase 5) | ❌ only Firefox is installed |

**Model gaps that block a model-only firmware (team decision, Gate 0 and 2):**
- The firmware must show the Incident state on the LEDs, but Incident has no
  getter in the class diagram. Either the team adds `state()` to Incident,
  as `examples/3-state-simple` does, or the firmware tracks the state itself
  (as the template's demo does).
- Button A = a door in AWAY → Warning: no class in the model combines the
  mode with the door event (System Operation page not converted). Either
  the team converts that page or adds the rule, or the firmware wiring
  holds it, which is a deviation.

- [x] Set up the micro:bit build (CODAL, as in the course template's
      `demos/microbit-library/firmware`): `firmware/build.sh`.
- [x] Compile `project/impl` unchanged (plus the C++11 table definitions),
      and add `io/input_driver`, `io/output_driver` and `io/serial_link` (spec §4).
- [x] Flash: the board starts and sends `hello` and `mode NONE`.
- [x] Button B: the owner resolves the newest active Incident (F15). Serial sends
      `incident` lines with id, severity and state (F16). Point 9.
- [x] Board test, 3 runs: every input matches the model (`tests-and-benchmarks.md`,
      `board-logs/`). The LEDs now show the most serious Incident, and every LED
      change is logged as a `display` line, so the patterns are checked too.
      **Gate 4 passed:** the user confirmed the LEDs (2026-10-27).
- [ ] Optional: a less sensitive smoke gesture (the shake also fires while the
      board is handled).
- [x] Firmware size: model 4.6 KB, board code 4.1 KB (`project/reports/tests-and-benchmarks.md`).
- [x] On-board latency: door 248 µs (HOME) / 407 µs (AWAY), smoke 331 µs, resolve 59 µs.
- [ ] Optional: the latency grows with the history, because every redraw copies all
      Incidents. Read only the newest active one.
- [x] Re-verify: alignment unchanged (class 76.7 %, sequence 83.3 %, states 100 %).

👁 **Gate 4:** the team tries every input on the board.

## Phase 5 – Database and dashboard

- [x] WebSerial connect (Chrome or Edge), and line parsing (spec §5): `website/dashboard/serial.js`.
- [x] Dexie database with `sessions`, `incidents` (updated in place, key `session/id`, because
      ids restart after a board reset) and `events` (spec §6): `db.js`.
- [x] Panels: LED mirror and mode, active Incidents, Incident/Event History, on-board
      latency, event log, database (export, import, sample data, clear): `index.html`, `app.js`.
- [x] Linked from the landing page (DASHBOARD). Pages publishes `website/`, so it will be at `/dashboard/`.
- [x] Works without our PC: the page offers the firmware `.hex` for download, with steps for
      flashing your own micro:bit. Everything runs in the visitor's browser.
- [x] Terminal flash commands on the dashboard for Windows, macOS and Linux, built from the page's
      own address. The Linux command was tested (download plus flash); Windows and macOS are untested.
- [ ] **Team:** merge to `main` so GitHub Pages publishes it (only `main` is deployed).
- [x] Tested with the board in Mozilla's Firefox 159 (WebSerial since 151): it connected and worked
      (user, 2026-10-27). The IndexedDB file shows 1 session, 5 Incidents in 5 rows (updated in
      place) and 39 events. **Gate 5 passed.**

👁 **Gate 5:** the team runs the demo flow end to end: board → serial →
database → dashboard.

## Phase 6 – Quality report and final verification

- [ ] `project/reports/quality-review.md` (spec §8).
- [ ] Final verifier run, and the final `fom.csv` row.
- [ ] Two-level verification (assignment 1, step 4): the AI generates a
      use case and an activity diagram **from the code**, and the team
      compares them by eye with `model/use-case-diagram` and
      `model/activity-diagram`. These two cannot be verified automatically.
- [ ] Optional: the board shows every Incident still on it; the dashboard keeps all of them.
- [x] Plot `fom.csv` to `project/reports/fom.png` with `project/reports/plot_fom.py`: alignment
      per diagram, open deviations and unit-test checks, 9 points (slide 2).

👁 **Gate 6:** the team reads the quality report and checks it against the
commits.

## Phase 7 – Presentation

- [ ] 5 slides:
  1. Group and problem: unattended cabins, frozen pipes, fire, break-ins.
  2. FoM: what we measure, and the chart.
  3. Verification: the verifier report and comparison drawing,
     deviations, tests.
  4. One feature with a code snippet, for example the Warning → Critical
     upgrade of the same Incident (the transition table).
  5. Conclusion and lessons learned (`WORKFLOW.md` has the full story).
- [ ] 30-second video: AWAY → button A → Warning → shake → Critical →
      button B → resolved → dashboard history.
- [ ] Rehearse the demo within 10 minutes.

👁 **Gate 7:** a team dry run.

## Suggested split (adjust to the team)

| Person | Area |
|--------|------|
| A | Model decisions (Gate 1–2), FoM chart |
| B | Unit tests and benchmarks |
| C | Firmware and serial |
| D | Dashboard and database |
| All | Slides, video, demo |
