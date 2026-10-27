# Deviation log

A deviation is a point where the converted model or the implementation could
not be read 1:1 from the UML diagrams and ADRs in `model/`, because they were
unclear, ambiguous, incomplete or contradicted each other. Rules are in
[CLAUDE.md](../../CLAUDE.md#deviations).

**Resolution order:** UML and ADR first, then `model/Team_Guide.md` as the
fallback, then an AI assumption as the last resort. AI assumptions stay open
until the team decides them. On 2026-10-27 the team reviewed all 13: it kept
10 and changed 3 (D09, D14, D15).

Notation changes forced by the verifier are not deviations. They are listed in
[the conversion README](../diagrams/conversion/README.md).

| Source | Count |
|--------|------:|
| Team Guide | 12 |
| Team decision (was an AI assumption) | 13 |
| AI assumption, open for the team | 0 |
| **Total** | **25** |

An AI assumption is **not** a resolution. The team's review of all 13, with the
answer for each, is in [ai-assumptions-review.md](ai-assumptions-review.md).

| ID | Where | Unclear in the UML or ADR | Resolution | Source |
|----|-------|---------------------------|------------|--------|
| D01 | Class diagram | The 8 lines between classes have no arrowheads, so it is not clear which class refers to which | Owner → owned or used: Owner → Cabin, Contact and Incident; Cabin → Sensor; System → Cabin, Sensor and Incident; History → Incident | Team Guide §1, §2, §3, §7, §9, §13 |
| D02 | Class diagram | The 8 associations have no role names, but in C++ each one is a named member | Named after the target class (`cabins`, `contacts`, `incidents`, `sensors`, `cabin`) | Team decision (2026-10-27): keep |
| D03 | Class diagram | HytteOwner–EmergencyContact and HytteOwner–Incident have no multiplicity | `*` for both: the owner configures contacts (plural) and views and resolves Incidents | Team Guide §2, §8, §13 |
| D04 | Class diagram | MonitoringSystem–Cabin has no multiplicity | `1`: one monitoring system per cabin | Team decision (2026-10-27): keep |
| D05 | Class diagram | `Incident.timestamp` has type `DateTime`, which is not defined anywhere | `string` | Team decision (2026-10-27): keep |
| D06 | Class diagram | `Sensor` is `<<abstract>>` but has no abstract method, which C++ requires | `detectCondition()` made abstract: each subclass has its own detection. Side effect: every subclass must override it, which shows as 8 Extra methods in the class report | Team decision (2026-10-27): keep |
| D07 | Implementation | `Cabin.changeMode()` takes no parameter, so the target mode is not given | Switches HOME ⇄ AWAY | Team Guide §6 |
| D08 | Implementation | What `Sensor.monitor()` does is not specified | Detects the condition only while the sensor is enabled | Team Guide §4 |
| D09 | Implementation | The guard `contactsConfigured` needs Incident to know the owner's contacts, but the class diagram gives Incident only a dependency on EmergencyContact | Was: the guard returns `false`. **Changed:** `Incident --> "*" EmergencyContact : contacts` replaces the dependency, and `registerIncident(severity, contacts)` gives each new Incident the system's contacts. The guard is true while at least one contact exists, and `notifyContacts()` notifies them (Team Guide §10–§12) | Team decision (2026-10-27): change |
| D10 | Implementation | What `MonitoringSystem.evaluateEvent()` does is not specified | Calls `monitor()` on every sensor, then `createIncident()` and `escalateIncident()` as the sequence diagram shows. Every event is treated as Critical smoke (mock-up) | Team decision (2026-10-27): keep |
| D11 | Sequence diagram | The lifelines *Communication Service* and *Emergency Service* are not classes in the class diagram | Left out of the verified scenario. They are external systems, and the delivery they do is simulated | Team Guide §16, §17 |
| D12 | Sequence diagram | The messages are prose, not method names | Each one mapped to a class diagram method (`evaluateEvent`, `createIncident`, `registerIncident`, `escalateIncident`, `receiveNotification`, `updateIncident`) | Team Guide §7, §9, §12 |
| D13 | Sequence diagram | *Register* and *Update Incident/Event History* are drawn as MonitoringSystem self-messages, but the class diagram puts these methods on `IncidentHistory` | `IncidentHistory` lifeline added, and the calls go to it | Team Guide §9 |
| D14 | Sequence and class diagram | The sequence has MonitoringSystem call IncidentHistory and EmergencyContact, but the class diagram has no relation from MonitoringSystem to either class | Was: two associations in the code only (2 Extra). **Changed:** `MonitoringSystem --> "1" IncidentHistory : history` and `MonitoringSystem --> "*" EmergencyContact : contacts` added to the class diagram | Team decision (2026-10-27): change |
| D15 | Sequence and class diagram | *Send / Deliver Critical Notification* to the owner, but `HytteOwner` has no method to receive a notification | Was: message left out. **Changed:** `+receiveNotification() void` added to `HytteOwner` (Team Guide §7). The message is still not in the scenario, because nothing in the model links MonitoringSystem to HytteOwner (finding F18) | Team decision (2026-10-27): change |
| D16 | State machine, System Operation page | The mode arrows (*owner selects HOME / AWAY*) have no action, so it is not clear how the class diagram's `Cabin.mode` attribute follows the state | Each arrow that changes the mode has the action `/ changeMode` (which switches HOME ⇄ AWAY, D07). `Awaiting → Home` has none, because `mode` starts as HOME | Team Guide §6 |
| D17 | State machine, System Operation page | The door and motion rule is only a note on the AWAY state (*Enabled Door/Motion monitoring can create security Warnings*), not a transition | Self-transitions `doorOpened` and `motionDetected / reportSecurityWarning` on `Away` and `AwayCold`; none on HOME, where they are ignored. The *Enabled* condition is not modelled, because no class holds per-sensor enabling for the owner | Team Guide §6 |
| D18 | Class diagram (F03 decision) | The decided line Cabin → MonitoringSystem has no role name or multiplicity | Role `system`, multiplicity `1`: one cabin, one monitoring system (matches D04) | Team decision (2026-10-27): keep |
| D19 | Implementation (F03 decision) | Which MonitoringSystem method a security Warning should call is not drawn | `reportSecurityWarning()` calls `createIncident()`: the system creates the Incident | Team Guide §7 |
| D20 | Implementation (F10 decision) | `registerIncident()` has no parameters, so it is not clear what it registers | It creates the new Incident and keeps it: an Incident is registered in the history when it is created | Team Guide §9 |
| D21 | Implementation (F10 decision) | A new Incident needs an id and a timestamp, but nothing supplies them | Id `I-1`, `I-2`, … in order, counted by a function-local counter (the class diagram has no attribute for it), so ids are never reused after old Incidents are dropped; timestamp empty (the micro:bit has no clock, see D05) | Team decision (2026-10-27): keep |
| D22 | Class diagram (F13 decision) | The decided history limit has no size and no rule for what is dropped | `maxIncidents = 20`. When full, the oldest *closed* Incident is dropped, or else the oldest. The dashboard database keeps all of them | Team decision (2026-10-27): keep |
| D23 | Implementation (F11 decision) | Which severity each event creates is not drawn | Smoke (`evaluateEvent()`, the `smoke_escalation` path) creates a CRITICAL Incident; a door or motion event in AWAY creates a WARNING | Team Guide §6, §7, §12 |
| D24 | Class diagram (F15 decision) | The new line HytteOwner → IncidentHistory has no role name or multiplicity | Role `history`, multiplicity `1`: the owner has one cabin system and so one history | Team decision (2026-10-27): keep |
| D25 | Implementation (F15 decision) | What `findIncident()` returns when no Incident has that id (for example one dropped by the limit, F13) is not drawn | Returns no Incident (a null pointer), and `resolveIncident()` then does nothing | Team decision (2026-10-27): keep |

## Findings and team decisions

Findings are gaps or contradictions in the model that need a **team
decision**, not a deviation. A decided finding is applied by the AI to the
**official model** (`project/diagrams/conversion/*.mmd`) and logged here. The
assignment 1 diagrams in `model/` are frozen and are not updated (see
[CLAUDE.md](../../CLAUDE.md#ground-truth)).

| ID | Finding | Decision | Status |
|----|---------|----------|--------|
| F01 | The firmware must show the Incident state on the LEDs, but the class diagram has no way to read it | Add `+state() State` to `Incident` (decided by the user, 2026-10-27) | Applied to the official model |
| F02 | The rule "a door in AWAY creates a Warning" is only on the *System Operation* state machine page, which was not converted | Convert the page (decided by the user, 2026-10-27): `state-cabin`, `state-monitoring_system` | Applied to the official model |
| F03 | In `state-cabin`, the Cabin reports a security Warning, but the class diagram gives Cabin no link to `MonitoringSystem` or `Incident`, so no Incident can be created from it | Add the association `Cabin --> "1" MonitoringSystem : system` (decided by the user, 2026-10-27). Details D18, D19 | Done in the conversion (class 76.5 %, the new relation is identical). Applied to the official model |
| F04 | The LEDs must also show HOME / AWAY, and `Cabin` has the same gap as F01 | `+state() State` added to `Cabin` together with F02, following the same decision as F01 | Confirmed by the user, 2026-10-27. Applied to the official model |
| F05 | The class diagram does not show the state machine members of Incident, Cabin and MonitoringSystem (`state`, `handle()`, guards, actions): 17 Extra in the class report | Open: add them to the class diagram, as the template's examples do | Open |
| F06 | Sequence vs class diagram: MonitoringSystem calls IncidentHistory and EmergencyContact without a relation (D14): 2 Extra | Add `MonitoringSystem --> "1" IncidentHistory : history` and `MonitoringSystem --> "*" EmergencyContact : contacts` (decided by the team in the review of D14, 2026-10-27) | Applied to the official model (class 80.0 %, both identical) |
| F07 | `Incident ..> EmergencyContact` is drawn, but no Incident method uses EmergencyContact: 1 Missing | Replace it with `Incident --> "*" EmergencyContact : contacts`, and give `registerIncident()` the parameter `contacts: vector<EmergencyContact>`, so the guard `contactsConfigured` can be real (decided by the team in the review of D09, 2026-10-27) | Applied to the official model (0 Missing) |
| F08 | The sensor subclasses must override `detectCondition()` (D06), which they do not show: 8 Extra | Open | Open |
| F09 | ADR-001 is not testable: the class diagram has no way to disable a sensor and no thresholds | Open | Open |
| F10 | No class owns `Incident` objects: every line to Incident is a plain association (MonitoringSystem, IncidentHistory, HytteOwner). So `createIncident()` has nowhere to keep a new Incident | `IncidentHistory *-- "*" Incident : incidents`, a composition (decided by the user, 2026-10-27). Details D20, D21 | Done in the conversion (the relation is identical). Applied to the official model |
| F11 | The new Incident's severity cannot be set: `createIncident()` and `registerIncident()` have no parameters, so nothing in the model can say Warning (door) or Critical (smoke) | `createIncident(severity: Severity)` and `registerIncident(severity: Severity)` (decided by the user, 2026-10-27). The history starts the Incident with `warningDetected` or `criticalDetected` (D23) | Applied to the official model |
| F12 | The firmware and the dashboard cannot read the Incidents: `viewHistory()` returns nothing, and the history has no getter | `viewHistory(): vector<Incident>` returns a copy of every Incident on the board, oldest first (decided by the user, 2026-10-27) | Applied to the official model |
| F13 | The history grows without limit (Team Guide §9: all Incidents are stored). Each Incident is about 80 bytes plus allocation overhead on the PC. The micro:bit has 128 KB of RAM | Limit the history (decided by the user, 2026-10-27): attribute `-maxIncidents: size_t` on IncidentHistory (D22). The board keeps the latest 20; the dashboard database keeps everything. The user may move long-term storage to DoltHub later | Applied to the official model |
| F14 | Sequence vs implementation: the new Incident must be told its severity (`IncidentHistory → Incident : handle()`, F11), but the team's sequence diagram (*Create Critical Incident*) does not draw that call. `smoke_escalation` dropped from 100 % to 83.3 % (1 extra message, 1 extra lifeline) | Open. Options: the team adds the message and the Incident lifeline to the sequence diagram, or the severity is set in the Incident's constructor (constructors are never messages) | Open |
| F15 | Button B (the owner resolves) cannot go through the model: `HytteOwner.resolveIncident()` has no parameter, and since IncidentHistory owns the Incidents with `unique_ptr` (F10), the `weak_ptr` associations from HytteOwner and MonitoringSystem to Incident can never point at them. Nothing in the model can reach a live Incident to resolve it | Open. Options: `IncidentHistory.updateIncident()` gets parameters (for example the id and an event), or HytteOwner resolves through the history, or the history's composition becomes an aggregation (`shared_ptr`) so the associations work | Decided 2026-10-27: the user asked the AI to "fix button B" and left the design to it. The AI chose, following Team Guide §8: `HytteOwner.resolveIncident(incidentId: string)`, a new line `HytteOwner --> "1" IncidentHistory : history`, and `IncidentHistory.findIncident(incidentId: string): Incident`. The owner finds the live Incident, fires `ownerResolved` (state machine: closes it), then calls `updateIncident()` (D24, D25). The `HytteOwner --> "*" Incident` line stays, but it cannot hold Incidents owned by the history. Applied to the official model; **the team may still choose another design** |
| F16 | The dashboard needs each Incident's id and severity to update its row, but the class diagram gives Incident no getter for either (only `state()`, F01). The board sends the states only | `+getId() string` and `+getSeverity() Severity` on Incident (decided by the user, 2026-10-27) | Applied to the official model |
| F17 | Seen on the board (Gate 4): every shake creates a **new** Critical Incident, so one smoke event shaken 4 times gave 4 Incidents. The model has no rule for "this condition already has an active Incident"; Team Guide §7 only covers upgrading a Warning to Critical | Open. Options: a repeated detection while an Incident for the same sensor is active updates that Incident, or it is ignored | Open |
| F18 | The team decided that `HytteOwner` can receive a notification (`+receiveNotification() void`, review of D15, 2026-10-27), applied to the official model. But the scenario still cannot send it: no class that sends notifications (MonitoringSystem or Incident) has a line to `HytteOwner` | Open. Options: add a line such as `MonitoringSystem --> "1" HytteOwner : owner` and the message to the sequence diagram, or leave the owner's notification to the board's LED screen and the dashboard | Open |
