# Assignment 2 – Requirements and Example Analysis

Background notes for turning the Hytte Monitoring mock-up into a tiny IoT system.

## What the assignment asks for

Assignment 2 extends the assignment 1 mock-up into a tiny IoT system on a
microcontroller, using model-driven AI design. The team stays the same.

| Area | Requirement |
|------|-------------|
| System | 1 sensor (button, microphone or accelerometer) and 1 actuator (LED, motor, speaker, ...) |
| System | The assignment 1 design runs on the microcontroller |
| Verification | One or more unit tests and benchmarks |
| Verification | Automated model extraction and deterministic verification (as in assignment 1) |
| Verification | A Figure of Merit (FoM) tracked over time, with at least 3 data points and a baseline first |
| Control | Input models structured so iteration is easy ("models as executable program") |
| Control | Code split into folders, one responsibility per file (SRP) |
| Understanding | A small mock-up or real database filled by interacting with the microcontroller |
| Understanding | A browser dashboard that connects over WebSerial and shows data from the database |
| Understanding | 5 slides, a 30-second video and a demo (max 10 minutes) |

The goal is still a mock-up, not a functional product. Only enough code is
needed to read one input and drive one output on the board.

## Reference example (aiunderstand/ModelDrivenDesign_ex2)

- Repo: https://github.com/aiunderstand/ModelDrivenDesign_ex2
- Demo: https://aiunderstand.github.io/ModelDrivenDesign_ex2/microbit/

### Verification pipeline

1. A person draws class, state and sequence diagrams in draw.io (`diagrams/input/`).
2. An AI writes the C++ implementation (`impl/`), guided by `AGENTS.md`.
3. `tools/verify.py` extracts the implemented design from the code using
   libclang, with no AI involved. Sequence diagrams are recorded by running
   scenario programs.
4. The tool writes a report with an **alignment score** (`reports/`) and a
   colour-coded draw.io comparison (`diagrams/output/`).
5. The same input always gives the same report, so the check is deterministic.

The mapping rules between UML and C++ are in `tools/umlverify/docs/UML-CPP-MAPPING.md`.

### Folder layout per design

```
diagrams/input/    class.drawio, state-<class>.drawio, sequence-<scenario>.drawio
impl/              CMakeLists.txt, include/, src/, scenarios/
diagrams/output/   <design>-design.mmd, <design>-comparison.drawio
reports/           <design>-report.md
```

### micro:bit demo (`demos/microbit-library`)

- Input: tilt (accelerometer) to select, button A lends, button B returns.
- Output: the board shows the current state.
- Link: WebSerial in Chrome or Edge.
- Storage: IndexedDB through Dexie.js, with export, import and clear.
- Extra: an "Ask the history" panel where Claude answers questions using
  read-only queries. This is optional and not required by the assignment.

## Consequences for Hytte Monitoring

- **Diagram coverage.** The verifier handles class, state and sequence
  diagrams. Our use case and activity diagrams cannot be verified
  automatically, so they stay as documentation.
- **Diagram format.** Our existing `.drawio` files were drawn freely. They
  probably need to be redrawn or adjusted to match the verifier's
  conventions before the tool can parse them. Check this first.
- **"Assignment 1 code".** Assignment 1 produced UML models and a static
  landing page, with no system logic in code. For us, "the code of
  assignment 1 runs on the microcontroller" therefore means the C++
  implementation of our class and state diagrams, compiled for the board.
- **Ground truth.** `model/Team_Guide.md` stays the source of truth. Mapping
  real buttons to simulated sensors is a group decision under Team Guide §19.

## Open questions for the team

1. Which board: micro:bit v2 (recommended, everything built in, matches the
   example) or Arduino Mega (needs wiring)?
2. Which simulated sensor do the board inputs represent? (proposal in the spec)
3. Which FoM do we use? (proposal: alignment score from `verify.py`)
4. Do we include the optional "Ask the history" AI panel?
