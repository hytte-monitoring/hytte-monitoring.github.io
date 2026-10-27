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
      rules in `project/reports/test-and-benchmark-report.md`.
- [x] `tests_passed` recorded in `fom.csv` (point 4).
- [ ] ADR-001, the HOME/AWAY door rule and ADR-002 are **not testable**
      with the current model. The team decides what to add to the model
      (see the report).

👁 **Gate 3:** the team runs the tests themselves (`ctest`) and checks
that they test the model, not the implementation's own guesses.

## Phase 4 – Firmware on the micro:bit

- [ ] Set up the micro:bit build (CODAL, as in the course template's
      `demos/microbit-library/firmware`).
- [ ] Compile `project/impl` unchanged, and add `io/input_driver`,
      `io/output_driver` and `io/serial_link` (spec §4).
- [ ] Flash, and check each row of the spec §3 tables on the board.
- [ ] On-board benchmark: button press to LED, and firmware size.
- [ ] Re-verify: alignment must not drop because of firmware needs.

👁 **Gate 4:** the team tries every input on the board.

## Phase 5 – Database and dashboard

- [ ] WebSerial connect (Chrome or Edge), and line parsing (spec §5).
- [ ] Dexie database with `events` and `incidents` (updated in place) (spec §6).
- [ ] Panels: live board state, event log, Incident/Event History, and
      export, import and clear.
- [ ] Link from the landing page; check it is served by GitHub Pages
      (`.github/workflows/static.yml`).

👁 **Gate 5:** the team runs the demo flow end to end: board → serial →
database → dashboard.

## Phase 6 – Quality report and final verification

- [ ] `project/reports/quality-report.md` (spec §8).
- [ ] Final verifier run, and the final `fom.csv` row.
- [ ] Plot `fom.csv` (alignment per diagram and deviations over time) to
      `project/reports/fom.png`.

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
