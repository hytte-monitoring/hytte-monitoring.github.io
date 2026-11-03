# CLAUDE.md

Instructions for AI agents working in this repository. The C++ rules are in
[AGENTS.md](AGENTS.md); this file adds what is specific to Hytte Monitoring.

## Ground truth

| What | Where | Status |
|------|-------|--------|
| **Official model** (class, state, sequence) | `project/diagrams/conversion/*.mmd`. These are the source; `convert.py` generates `project/diagrams/input/*.drawio`, which the verifier reads. Never edit the generated `.drawio` by hand | **Living.** Changed only on a team decision (see below) |
| **ADRs** | `model/adr/` | **Living.** Changed only on a team decision |
| **Assignment 1 diagrams** | `model/*-diagram/` (`.drawio`, `.png`) | **Frozen.** A record of the starting point. Never edited again. The use case and activity diagrams live only here; they are documentation, because the verifier cannot check them |
| **Fallback** | `model/Team_Guide.md` | Used when the official model or an ADR is unclear |

Resolution order when something is unclear:

1. **The official model and the ADRs.**
2. **Fallback: `model/Team_Guide.md`.** When a diagram or ADR is unclear,
   ambiguous, incomplete, or contradicts another diagram, use the Team Guide
   to resolve it instead of asking the team.
3. **Last resort: an AI assumption.** If the Team Guide does not settle it
   either, make the smallest reasonable assumption and flag it for the team.

### Who may change the official model and the ADRs

- **The AI applies changes only on an explicit team decision.** It never
  changes the model or an ADR on its own, and never to make its own code
  pass the verifier. A mismatch between model and code is reported as a
  deviation or a finding, not fixed in the model.
- **Every change is logged** in the *Findings and team decisions* table of
  `project/reports/deviations.md`: what changed, why, who decided, and when.
  It is committed separately from code changes, so the team can review the
  diff.
- **The team may also edit the `.mmd` files themselves.** Then run
  `python3 project/diagrams/conversion/convert.py` and commit.
- This is a deliberate choice (decided by the user, 2026-10-27). Assignment 1
  says the input set is changed "manually by you". Here the team makes every
  decision, and the AI only applies and logs it. Explain this in the
  presentation.

## Deviations

A **deviation** is any point where the official model or the implementation
cannot be read 1:1 from the diagrams and ADRs, because they are not clear,
and had to be resolved by the Team Guide or by an assumption.

- Log every deviation in `project/reports/deviations.md` when it is made, with
  an ID, the unclear UML or ADR element, the resolution, and its source
  (`Team Guide §n` or `AI assumption`).
- Notation changes forced by the verifier (supported shapes, C++ type names,
  `1..*` → `*`) are not deviations; they are listed in
  `project/diagrams/conversion/README.md`.
- The number of deviations is recorded in `project/reports/fom.csv` at every data
  point: `deviations` (all), `deviations_team_guide` (settled by the Team Guide) and
  `deviations_ai_open` (AI assumptions not yet decided by the team).
- An AI assumption is **not** a resolution. When the team decides one (see
  `project/reports/ai-assumptions-review.md`), change its source to
  `Team decision (date)` in `deviations.md`, and update the review file and the counts.
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

- Document every step in the workflow log: what, why, commands, sources fetched,
  programs installed, results, commits. Add the user's prompt for the step to
  its **Prompt log**. The log is local only, outside the repo:
  `~/Documents/Hytte-Monitoring-WORKFLOW.md` (moved there by the user's
  decision, 2026-10-28). Never add it back to the repo.
- Commit locally in normal-sized commits: one per logical change, grouping related
  edits (a fix with its reports, FoM row and log entry). Not one per small detail.
  Short imperative message. Never push.
- The assignment guides are local only, outside the repo:
  `~/Documents/Assignment_1_Guide.md` and `~/Documents/Assignment_2_Guide.md`
  (moved there by the user's decision, 2026-10-28). Never add them to the repo.
