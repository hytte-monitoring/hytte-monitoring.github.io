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
| `state-cabin.mmd`, `state-monitoring_system.mmd` | The System Operation page, flattened per owning class, the sources for `../input/state-cabin.drawio` and `../input/state-monitoring_system.drawio` |
| `sequence-smoke_escalation.mmd` | One path through the sequence diagram, the source for `../input/sequence-smoke_escalation.drawio` |
| `convert.py` | Draws both `.drawio` files using the verifier's own draw.io writer |

To regenerate, run `python3 project/diagrams/conversion/convert.py`. To change
the design, edit the `.mmd` files, run the script, and commit all of it.

Round trip check: the verifier reads the generated files back as exactly the
same model as the `.mmd` sources (18 classes and 17 relations; 4 states and
9 transitions).

## Class diagram: what changed and why

All 18 classes, every attribute, every method and every enumeration value
are kept with the team's names. Class positions follow the team's layout.
The table lists every change. Changes that resolve an unclear point in the
UML are **deviations**, logged with their source in
[`project/reports/deviations.md`](../../reports/deviations.md). The rest are
notation only.

| Change | Original | Converted | Why |
|--------|----------|-----------|-----|
| Shapes | Rectangles with HTML text | UML class shapes (swimlane plus one row per member) | The only shape the verifier reads |
| Type names | `String`, `Boolean`, `Float` | `string`, `bool`, `float` | The C++ types the verifier compares against |
| `Incident.timestamp` | `DateTime` | `string` | Deviation D05 |
| Return types | none drawn | `void` | The verifier treats a missing return type as `void` anyway; it is written out to make it explicit |
| `Sensor.detectCondition()` | plain | abstract (`*`) | Deviation D06 |
| Plain lines between classes | no arrowheads, no names | one-way association `-->` with a role name | Deviations D01 and D02 |
| Multiplicity `1..*` | `1..*` | `*` | The verifier only knows `1`, `0..1` and `*` |
| Multiplicity not drawn | none on Owner–Contact, Owner–Incident, System–Cabin | `*`, `*`, `1` | Deviations D03 and D04 |

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

The *System Operation* page is converted separately; see the next section.

## System Operation page: split by owning class (team decision F02)

The page has one composite state, *Operating*, with four concurrent regions.
Each region was given to the class that owns its attribute in the class
diagram, and each class's regions were flattened into one machine (the
product of their states).

| Region | Owner (attribute) | Machine |
|--------|-------------------|---------|
| MONITORING MODE: Awaiting mode selection, HOME, AWAY | `Cabin` (`mode`) | `state-cabin`: 3 × 2 = 6 states |
| COLD-WEATHER PROTECTION: inactive, active | `Cabin` (`coldProtectionActive`) | |
| POWER SOURCE: Cabin electricity, Battery backup | `MonitoringSystem` (`onBatteryBackup`) | `state-monitoring_system`: 2 × 2 = 4 states |
| COMMUNICATION CHANNEL: Normal Internet, Cellular/SIM | `MonitoringSystem` (`cellularFallback`) | |

**state-cabin** (6 states, 18 transitions). States `Awaiting`, `Home` and
`Away`, each with a `…Cold` twin while protection is active.

| Transition | From the original |
|------------|-------------------|
| `ownerSelectsHome`, `ownerSelectsAway` (8 arrows, in both protection states) | *owner selects HOME / AWAY*. The `/ changeMode` action keeps the `mode` attribute in step (deviation D16) |
| `coldRequired / activateColdProtection` (3 arrows) | `when(coldRequired)`, and the entry action of *Protection active*: save the choices, make them mandatory |
| `coldGone / deactivateColdProtection` (3 arrows) | `when(not coldRequired)`, and the exit action: restore the saved choices |
| `doorOpened`, `motionDetected / reportSecurityWarning`, in `Away` and `AwayCold` (4 self-arrows) | The note on AWAY: *Enabled Door/Motion monitoring can create security Warnings*. HOME has no such arrow, so door and motion are ignored there (deviation D17) |

**state-monitoring_system** (4 states, 8 transitions). Each `powerLost`,
`powerRestored`, `internetLost` and `internetRestored` arrow comes from a
`when(...)` arrow. Its action (`useBatteryBackup`, `useCabinElectricity`,
`useCellular`, `useInternet`) comes from the target state's `entry /` line.

**Notation changes (verifier limits):**
- `entry` / `exit` actions became transition actions.
- `when(...)` change events became named events.
- The choice pseudo-states at the start of the cold, power and internet
  regions (`[coldRequired]`, `[powerOK]`, `[internetOK]`) became plain
  initial states (`Awaiting`, `ElectricityAndInternet`). A cabin that starts
  in the cold, or on battery, gets the event right after start.

**Left out:**
- The entry note of *Awaiting mode selection* (ask the owner).
- The *Operating* composite's internal transitions (*condition requires
  attention / create Incident*, *Warning worsens / upgrade*). These are
  covered by the Incident state machine and the sequence diagram.
- The *Enabled* condition on door and motion (see D17).

**Class diagram changes (team decisions):**
- F01, F04: `+state() State` was added to `Incident` and `Cabin`. The
  firmware needs it to show the state on the LEDs.
- F03: the association `Cabin --> "1" MonitoringSystem : system` was
  added, so a door or motion Warning in AWAY can reach `createIncident()`
  (D18, D19).
- F10: `IncidentHistory --> "*" Incident` became the composition
  `IncidentHistory *-- "*" Incident`: the history owns every Incident (D20,
  D21).
- F11: `createIncident(Severity severity)` and
  `registerIncident(Severity severity)` (D23).
- F12: `viewHistory()` returns `vector<Incident>`.
- F13: the attribute `-size_t maxIncidents` on IncidentHistory (D22). It is
  not `static`, because the verifier does not read static data members.

## Sequence diagram: which path, and how messages were mapped

The team's sequence diagram (`model/sequence-diagram/`) has 6 lifelines,
about 45 messages written as prose, and 8 `alt` / `opt` fragments. The
verifier does not support fragments, and it compares messages as method calls
between classes. The converted scenario is therefore **one path**,
`smoke_escalation`: smoke is detected, a Critical Incident is created, the
owner does not respond, and a Family/Emergency Contact is notified (Team
Guide §12).

| # | Converted message | Original message(s) |
|---|-------------------|---------------------|
| 1 | `SmokeSensor → MonitoringSystem : evaluateEvent()` | *Smoke Detected*, *Evaluate event and severity* |
| 2 | `MonitoringSystem → MonitoringSystem : createIncident()` | *Create Critical Incident* |
| 3 | `MonitoringSystem → IncidentHistory : registerIncident()` | *Register Incident in Incident/Event History* |
| 4 | `MonitoringSystem → MonitoringSystem : escalateIncident()` | *Wait system-determined waiting time* (no owner response), then *Send Critical Escalation* |
| 5 | `MonitoringSystem → EmergencyContact : receiveNotification()` | *Deliver Critical Escalation* |
| 6 | `MonitoringSystem → IncidentHistory : updateIncident()` | *Update existing Incident/Event History record* |

**Left out**, because of verifier limits:

- The other fragment paths: owner resolves, owner asks for Suggested Next
  Steps, the contact responds, Emergency Service escalation, and immediate
  danger.
- Return messages.

**Changes in meaning**, logged as deviations D11–D15 in
[`deviations.md`](../../reports/deviations.md):

- The Communication Service and Emergency Service lifelines are dropped.
- The owner notification is dropped.
- History messages are moved to an `IncidentHistory` lifeline.
- Prose messages are mapped to class diagram methods.

## Known gap at baseline

The state machine adds members to `Incident`: a `state` attribute,
`handle(event)`, and the guard and action methods. The class diagram does
not show them yet. This is intentional: the baseline measures the gap, and
adding them is an iteration.
