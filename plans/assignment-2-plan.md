# Assignment 2 – Plan

Related: `research/assignment-2-requirements.md`, `specs/assignment-2-iot-spec.md`.

## Phase 0 – Agree and set up (whole team)

- [ ] Agree on the board, the input mapping and the FoM (spec §1–2,
      research "Open questions").
- [ ] Borrow a micro:bit v2 and check that it flashes and talks over serial.
- [ ] Bring in the verifier from the example repo (`tools/`, `requirements.txt`,
      `AGENTS.md`), with credit to the source.
- [ ] Create the structure:
      `project/diagrams/input/`, `project/impl/`, `project/reports/`,
      `firmware/`, `website/dashboard/`.

## Phase 1 – Baseline (do this first, it is FoM data point 1)

- [ ] Adapt the class diagram, the Incident state machine and one sequence
      diagram to the verifier's draw.io conventions, and put them in
      `project/diagrams/input/`.
- [ ] Generate a first C++ implementation with AI from those inputs only.
- [ ] Run `verify.py` and commit the report. **This is the baseline score.**
- [ ] Start `reports/fom.csv` with columns `date, commit, class%, state%, sequence%, tests_passed`.

## Phase 2 – Close the gap (FoM data points 2, 3, ...)

- [ ] Fix differences found by the report, in the model or in the code,
      one fix per commit.
- [ ] Rerun `verify.py` after each iteration and add a row to `fom.csv`.
- [ ] Note any regressions honestly. The assignment says they are fine.

## Phase 3 – Tests and benchmark

- [ ] Write host-side unit tests for the rules in spec §8.
- [ ] Write a benchmark (latency of `evaluateEvent()`, firmware size) and
      save the result in `reports/`.
- [ ] Optional: a script that runs verification, tests and benchmark in one go.

## Phase 4 – Firmware on the board

- [ ] Add `io/InputDriver`, `io/OutputDriver` and `io/SerialLink`, keeping
      domain classes free of hardware code.
- [ ] Flash the board and check each row of the mapping table (spec §2–3).
- [ ] Check that the verifier score did not drop after adding the I/O code.

## Phase 5 – Database and dashboard

- [ ] Build the WebSerial connect panel based on the example template.
- [ ] Add a Dexie.js database with an `events` table and an `incidents`
      table that is updated in place.
- [ ] Add panels for live state, the event log and incident history, with
      export, import and clear.
- [ ] Link the dashboard from the landing page and check that GitHub Pages
      serves it.

## Phase 6 – FoM chart and presentation

- [ ] Plot `fom.csv` over time (at least 3 points) and save it as an image.
- [ ] Make the slides:
  1. Group and problem: unattended cabins, frozen pipes, fire, break-ins.
  2. FoM: what we measure, and the chart.
  3. Verification: verifier report, comparison diagram, tests.
  4. One feature with a code snippet, for example the Warning to Critical
     upgrade that keeps the same Incident.
  5. Conclusion and lessons learned.
- [ ] Record a 30-second video: press A in AWAY, see the Warning, shake to
      upgrade, press B to resolve, show the dashboard history.
- [ ] Rehearse the demo within 10 minutes.

## Suggested split (adjust to the team)

| Person | Area |
|--------|------|
| A | Diagrams for the verifier, FoM tracking |
| B | C++ domain classes and unit tests |
| C | micro:bit I/O and serial |
| D | Dashboard and database |
| All | Slides, video, demo |
