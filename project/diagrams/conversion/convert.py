"""Generate the verifier's input diagrams from the mermaid sources in this folder.

    python3 project/diagrams/conversion/convert.py

Reads class.mmd, the state-*.mmd files and sequence-smoke_escalation.mmd and writes
the matching .drawio files in diagrams/input/, drawn with the verifier's own writer so it
can read them back. Class positions follow the team's model/class-diagram layout.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools"))

from umlverify.class_diagram import drawio_write as class_write, mermaid as class_mmd  # noqa: E402
from umlverify.state_diagram import drawio_write as state_write, mermaid as state_mmd  # noqa: E402
from umlverify.sequence_diagram import drawio_write as seq_write, mermaid as seq_mmd  # noqa: E402

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
CABIN_LAYOUT = {
    "Awaiting": (80, 200, 130, 50),
    "Home": (380, 60, 130, 50),
    "Away": (380, 340, 130, 50),
    "AwaitingCold": (80, 560, 130, 50),
    "HomeCold": (740, 60, 130, 50),
    "AwayCold": (740, 340, 130, 50),
}

SYSTEM_LAYOUT = {
    "ElectricityAndInternet": (80, 80, 190, 50),
    "BatteryAndInternet": (520, 80, 190, 50),
    "ElectricityAndCellular": (80, 360, 190, 50),
    "BatteryAndCellular": (520, 360, 190, 50),
}

INCIDENT_LAYOUT = {
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

    for subject, layout, title in [("incident", INCIDENT_LAYOUT, "Incident"),
                                   ("cabin", CABIN_LAYOUT, "Cabin"),
                                   ("monitoring_system", SYSTEM_LAYOUT, "MonitoringSystem")]:
        machine = state_mmd.parse((HERE / f"state-{subject}.mmd").read_text())
        (INPUT / f"state-{subject}.drawio").write_text(
            state_write.document(machine, {"states": layout},
                                 name=f"Hytte Monitoring - {title} state machine"))

    scenario = seq_mmd.parse((HERE / "sequence-smoke_escalation.mmd").read_text())
    (INPUT / "sequence-smoke_escalation.drawio").write_text(
        seq_write.document(scenario, name="Hytte Monitoring - smoke escalation"))
    print("wrote class, state and sequence diagrams in", INPUT)


if __name__ == "__main__":
    main()
