# Firmware: Hytte Monitoring on a micro:bit v2

The model from `project/impl/` (headers and sources, **unchanged**) runs on the
board, wired to its buttons, accelerometer, LED matrix and USB serial port.
The board code in `src/` only translates between the hardware and the model.

```
src/main.cpp              wiring only: creates the model objects and the drivers
src/io/input_driver.*     buttons and shake -> model events
src/io/output_driver.*    model state -> 5x5 LED matrix
src/io/serial_link.*      model state -> JSON lines on USB serial (115200 baud)
build.sh                  builds MICROBIT.hex with CODAL; --flash copies it to the board
codal.json                the CODAL target, pinned to codal-microbit-v2 v0.3.5
```

`build.sh` and `codal.json` are adapted from `demos/microbit-library/firmware/`
in [aiunderstand/ModelDrivenDesign_ex2](https://github.com/aiunderstand/ModelDrivenDesign_ex2)
(commit `d439b1a`).

## Inputs and outputs (spec §3)

| Board | Model | Result |
|-------|-------|--------|
| Button A | `cabin.handle(doorOpened)` | In AWAY: a Warning Incident (`state-cabin`, F03, F11). In HOME: ignored |
| Shake | `monitoringSystem.evaluateEvent()` | A Critical Incident, and the contact is notified (`smoke_escalation`) |
| Buttons A+B | `cabin.handle(ownerSelectsAway / ownerSelectsHome)` | From HOME go AWAY, otherwise go HOME |
| Button B | – | **Not possible through the model yet** (finding F15). The board sends a `note` line |

| LED matrix | When |
|------------|------|
| `?` | No mode chosen yet (`Awaiting`) |
| `H` / `A` | HOME / AWAY, no active Incident |
| blinking `!` | The newest active Incident is a Warning |
| flashing full matrix | The newest active Incident is Critical |

## Serial lines (board → dashboard)

```
{"type":"hello","firmware":"hytte-monitoring 0.1"}
{"type":"mode","mode":"AWAY"}                      HOME, AWAY or NONE (Awaiting)
{"type":"event","sensor":"door","mode":"AWAY"}
{"type":"history","states":["Warning","Critical"]} every Incident on the board, oldest first
{"type":"latency","input":"door","us":123}          model update + LED redraw, in microseconds
{"type":"note","message":"..."}
```

`history` sends states only: the class diagram gives Incident no readable id
or severity (finding F16).

## Build and flash

```sh
firmware/build.sh --flash
```

- **Needs:** git, Python 3, CMake, and make or ninja.
- **First run:** downloads the Arm GNU toolchain 13.3.rel1 (about 130 MB)
  and CODAL into `firmware/.build/` (1.1 GB, git-ignored). That takes a few
  minutes.
- **After that:** a build takes seconds.
- **C++11:** CODAL compiles with `-std=c++11`. The model needed one change
  for that: an out-of-class definition of each `transitions` table, used
  only before C++17.
