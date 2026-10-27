# Diagram conversion

The verifier (`tools/verify.py`) cannot read the team's original diagrams in
`model/`.

- **Class diagram:** the classes are plain rectangles with HTML text inside,
  not draw.io's UML class shapes.
- **State machine:** it uses concurrent regions and `entry` / `exit`
  actions, which the verifier does not support.

This folder converts them into the format the verifier reads. The originals
in `model/` are unchanged and remain the full documentation.

| File | Role |
|------|------|
| `class.mmd` | The class diagram as mermaid text, the source for `../input/class.drawio` |
| `state-incident.mmd` | The flat Incident state machine, the source for `../input/state-incident.drawio` |
| `convert.py` | Draws both `.drawio` files using the verifier's own draw.io writer |

To regenerate, run `python3 project/diagrams/conversion/convert.py`. To change
the design, edit the `.mmd` files, run the script, and commit all of it.

Round trip check: the verifier reads the generated files back as exactly the
same model as the `.mmd` sources (18 classes and 17 relations; 4 states and
9 transitions).

## Class diagram: what changed and why

All 18 classes, every attribute, every method and every enumeration value
are kept with the team's names. Class positions follow the team's layout.
The changes below are notation only.

| Change | Original | Converted | Why |
|--------|----------|-----------|-----|
| Shapes | Rectangles with HTML text | UML class shapes (swimlane plus one row per member) | The only shape the verifier reads |
| Type names | `String`, `Boolean`, `Float` | `string`, `bool`, `float` | The C++ types the verifier compares against |
| `Incident.timestamp` | `DateTime` | `string` | C++ has no `DateTime` type, and the micro:bit has no clock |
| Return types | none drawn | `void` | The verifier treats a missing return type as `void` anyway; it is written out to make it explicit |
| `Sensor` attributes | `- sensorID`, `- enabled` (private) | `#` (protected) | Subclasses inherit them |
| `Sensor.detectCondition()` | plain | abstract (`*`) | `<<abstract>>` needs at least one abstract method in C++ |
| Plain lines between classes | no arrowheads, no names | one-way association `-->` with a role name | In C++ every relation is a member of one class, so it needs a direction and a name |
| Multiplicity `1..*` | `1..*` | `*` | The verifier only knows `1`, `0..1` and `*` |
| Multiplicity not drawn | none on Owner–Contact, Owner–Incident, System–Cabin | `*`, `*`, `1` | Taken from Team Guide §2, §13 and the class roles |

Direction of each association (owner → owned or used):

| Relation | Role | Reason |
|----------|------|--------|
| `HytteOwner --> "*" Cabin` | `cabins` | The owner has one or more cabins (the original was 1 to 1..*) |
| `HytteOwner --> "*" EmergencyContact` | `contacts` | The owner configures contacts (§13) |
| `HytteOwner --> "*" Incident` | `incidents` | The owner views and resolves incidents (§8) |
| `Cabin --> "*" Sensor` | `sensors` | A cabin has 1..* sensors (original multiplicity) |
| `MonitoringSystem --> "1" Cabin` | `cabin` | The system monitors one cabin |
| `MonitoringSystem --> "*" Sensor` | `sensors` | The system reads 1..* sensors (original multiplicity) |
| `MonitoringSystem --> "*" Incident` | `incidents` | The system creates 0..* incidents (original multiplicity) |
| `IncidentHistory --> "*" Incident` | `incidents` | History holds 0..* incidents (original multiplicity) |
| `Incident ..> EmergencyContact` | – | Kept as the team drew it: a dashed dependency |

## State machine: how it was flattened

The original *Incident Lifecycle* page has one composite state with three
concurrent regions: **SEVERITY**, **OWNER HANDLING** and **ESCALATION**. The
verifier needs one flat machine per class, so the converted machine is
`state-incident` for the class `Incident`.

| State | From the original |
|-------|-------------------|
| `New` | The start of the Incident, before its first severity is set. It replaces the guarded initial transitions `[initial severity = Warning]` and `[initial severity = Critical]`, because an initial transition cannot have a guard |
| `Warning` | SEVERITY: Warning |
| `Critical` | SEVERITY: Critical |
| `Closed` | Resolved / Closed |

| Transition | From the original |
|------------|-------------------|
| `New → Warning : warningDetected / notifyOwner` | Initial severity Warning; entry / notify owner |
| `New → Critical : criticalDetected / notifyOwner` | Initial severity Critical; entry / notify owner immediately |
| `Warning → Critical : conditionWorsens / upgradeToCritical` | Condition worsens: upgrade the SAME Incident |
| `Warning → Warning : ownerWaitingTimeout [contactsConfigured] / notifyContacts` | ESCALATION: after the owner waiting time → Contacts notified |
| `Critical → Critical : ownerWaitingTimeout [contactsConfigured] / notifyContacts` | Same, for Critical |
| `Critical → Critical : contactWaitingTimeout / contactEmergencyService` | After the contact waiting time → Emergency Service contacted (Critical only, §12) |
| `Critical → Critical : safetyOverride / contactEmergencyService` | criticalSafetyOverride: immediate critical danger bypasses waiting time |
| `Warning → Closed`, `Critical → Closed : ownerResolved / resolve` | Owner selects Resolved: close the SAME Incident |

**Left out**, because flattening them would multiply the number of states:

- The OWNER HANDLING sub-states (*Guidance offered*, *Guidance displayed*).
  These are handled by the dashboard as user interface.
- The *Critical and no contacts configured* path straight to the Emergency
  Service.
- Entry actions that update the History record. The verifier does not
  support `entry` actions.

The *System Operation* page (HOME/AWAY, cold-weather protection, power
source, communication channel) is not converted yet.

## Known gap at baseline

The state machine adds members to `Incident`: a `state` attribute,
`handle(event)`, and the guard and action methods. The class diagram does
not show them yet. This is intentional: the baseline measures the gap, and
adding them is an iteration.
