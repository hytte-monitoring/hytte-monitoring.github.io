# hytte-monitoring
Remote cabin monitoring mock-up developed using UML-based, specification-driven AI development.

## Layout
- `website/` — the static site (HTML, CSS, images)
- `model/` — UML diagrams of the system
- `research/` — background notes and findings
- `specs/` — written specifications
- `plans/` — implementation plans
- `project/` — assignment 2 verification project
  - `diagrams/input/` — draw.io diagrams the verifier reads (class, state, sequence)
  - `diagrams/output/` — generated comparison diagrams
  - `impl/` — C++ implementation of the model (`include/`, `src/`, `scenarios/`)
  - `reports/` — verifier reports and Figure of Merit data
- `firmware/` — micro:bit code (domain classes plus input/output/serial drivers)
- `website/dashboard/` — WebSerial dashboard and browser database

## Credits
The UML verifier (`tools/`, `requirements.txt`), `AGENTS.md` and the VS Code tasks in `.vscode/`
are copied from [aiunderstand/ModelDrivenDesign_ex2](https://github.com/aiunderstand/ModelDrivenDesign_ex2)
(commit `d439b1a`), the course template for assignment 2.
