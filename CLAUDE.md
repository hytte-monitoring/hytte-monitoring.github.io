# CLAUDE.md

Instructions for AI agents working in this repository. The C++ rules are in
[AGENTS.md](AGENTS.md); this file adds what is specific to Hytte Monitoring.

## Ground truth

1. **Input set: the UML diagrams in `model/` (`.drawio`) and the ADRs in
   `model/adr/`.** These are the design. The AI never edits them; only the
   team changes them, by hand.
2. **Fallback: `model/Team_Guide.md`.** When a UML diagram or ADR is unclear,
   ambiguous, incomplete, or contradicts another diagram, use the Team Guide
   to resolve it instead of asking the team.
3. **Last resort: an AI assumption.** If the Team Guide does not settle it
   either, make the smallest reasonable assumption and flag it for the team.

The verifier inputs in `project/diagrams/input/` are generated from
`project/diagrams/conversion/` (see its README). The conversion may change
notation only (shapes, C++ type names). Any change in meaning is a deviation.

## Deviations

A **deviation** is any point where the converted model or the implementation
cannot be read 1:1 from the UML diagrams and ADRs, because they are not clear,
and had to be resolved by the Team Guide or by an assumption.

- Log every deviation in `project/reports/deviations.md` when it is made, with
  an ID, the unclear UML or ADR element, the resolution, and its source
  (`Team Guide §n` or `AI assumption`).
- Notation changes forced by the verifier (supported shapes, C++ type names,
  `1..*` → `*`) are not deviations; they are listed in
  `project/diagrams/conversion/README.md`.
- The number of open deviations is recorded in the `deviations` column of
  `project/reports/fom.csv` at every data point.
- Report new deviations to the user before declaring a task done. Do not
  close an `AI assumption` deviation yourself; the team decides.

## Verify

After every change to `project/`, run `.venv/bin/python tools/verify.py project`,
read every report in `project/reports/`, and add a row to `fom.csv` for each
iteration (one commit per fix). Never edit generated files in
`project/diagrams/output/` or `project/reports/*-report.md`. The verifier
deletes every `reports/*-report.md` on each run, so never give a hand-written
file a name ending in `-report.md`.

## Workflow

- Document every step in `WORKFLOW.md`: what, why, commands, sources fetched,
  programs installed, results, commits. Add the user's prompt for the step to
  its **Prompt log**.
- Commit locally in normal-sized commits: one per logical change, grouping related
  edits (a fix with its reports, FoM row and log entry). Not one per small detail.
  Short imperative message. Never push.
- `Assignment_1_Guide.md` and `Assignment_2_Guide.md` are local only (listed in
  `.git/info/exclude`). Never commit them.
