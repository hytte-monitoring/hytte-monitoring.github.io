"""Generate the verifier's input diagrams from the mermaid sources in this folder.

    python3 project/diagrams/conversion/convert.py

Reads class.mmd and state-incident.mmd and writes diagrams/input/class.drawio and
diagrams/input/state-incident.drawio, drawn with the verifier's own writer so it
can read them back. Class positions follow the team's model/class-diagram layout.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools"))

from umlverify.class_diagram import drawio_write as class_write, mermaid as class_mmd  # noqa: E402
from umlverify.state_diagram import drawio_write as state_write, mermaid as state_mmd  # noqa: E402

INPUT = HERE.parent / "input"

# (x, y, width), taken from model/class-diagram/class-diagram.drawio
CLASS_LAYOUT = {
    "HytteOwner": (910, 0, 220),
    "MonitoringMode": (330, 230, 160),
    "Cabin": (610, 250, 240),
    "MonitoringSystem": (1210, 250, 240),
    "Incident": (2350, 250, 240),
    "IncidentHistory": (2700, 250, 220),
    "Sensor": (910, 520, 220),
    "EmergencyContact": (2700, 560, 220),
    "SmokeSensor": (105, 820, 210),
    "IndoorTemperatureSensor": (335, 820, 210),
    "OutdoorTemperatureSensor": (565, 820, 210),
    "WaterLeakSensor": (795, 820, 210),
    "DoorSensor": (1025, 820, 210),
    "MotionSensor": (1255, 820, 210),
    "PowerSensor": (1485, 820, 210),
    "ConnectionSensor": (1715, 820, 210),
    "Severity": (2350, 830, 160),
    "IncidentStatus": (2700, 830, 160),
}

# (x, y, width, height)
STATE_LAYOUT = {
    "New": (120, 220, 120, 50),
    "Warning": (420, 80, 140, 50),
    "Critical": (420, 360, 140, 50),
    "Closed": (820, 220, 120, 50),
}


def main():
    types, relations = class_mmd.parse((HERE / "class.mmd").read_text())
    (INPUT / "class.drawio").write_text(
        class_write.document(types, relations, {"classes": CLASS_LAYOUT, "edges": {}},
                             name="Hytte Monitoring - class diagram"))

    machine = state_mmd.parse((HERE / "state-incident.mmd").read_text())
    (INPUT / "state-incident.drawio").write_text(
        state_write.document(machine, {"states": STATE_LAYOUT},
                             name="Hytte Monitoring - Incident state machine"))
    print("wrote", INPUT / "class.drawio", "and", INPUT / "state-incident.drawio")


if __name__ == "__main__":
    main()
