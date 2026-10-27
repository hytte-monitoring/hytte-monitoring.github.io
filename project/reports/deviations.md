# Deviation log

A deviation is a point where the converted model or the implementation could
not be read 1:1 from the UML diagrams and ADRs in `model/`, because they were
unclear, ambiguous, incomplete or contradicted each other. Rules are in
[CLAUDE.md](../../CLAUDE.md#deviations).

**Resolution order:** UML and ADR first, then `model/Team_Guide.md` as the
fallback, then an AI assumption as the last resort. AI assumptions stay open
until the team confirms them.

Notation changes forced by the verifier are not deviations. They are listed in
[the conversion README](../diagrams/conversion/README.md).

| Source | Count |
|--------|------:|
| Team Guide | 9 |
| AI assumption, open for the team | 8 |
| **Total** | **17** |

| ID | Where | Unclear in the UML or ADR | Resolution | Source |
|----|-------|---------------------------|------------|--------|
| D01 | Class diagram | The 8 lines between classes have no arrowheads, so it is not clear which class refers to which | Owner → owned or used: Owner → Cabin, Contact and Incident; Cabin → Sensor; System → Cabin, Sensor and Incident; History → Incident | Team Guide §1, §2, §3, §7, §9, §13 |
| D02 | Class diagram | The 8 associations have no role names, but in C++ each one is a named member | Named after the target class (`cabins`, `contacts`, `incidents`, `sensors`, `cabin`) | AI assumption |
| D03 | Class diagram | HytteOwner–EmergencyContact and HytteOwner–Incident have no multiplicity | `*` for both: the owner configures contacts (plural) and views and resolves Incidents | Team Guide §2, §8, §13 |
| D04 | Class diagram | MonitoringSystem–Cabin has no multiplicity | `1`: one monitoring system per cabin | AI assumption |
| D05 | Class diagram | `Incident.timestamp` has type `DateTime`, which is not defined anywhere | `string` | AI assumption |
| D06 | Class diagram | `Sensor` is `<<abstract>>` but has no abstract method, which C++ requires | `detectCondition()` made abstract: each subclass has its own detection. Side effect: every subclass must override it, which shows as 8 Extra methods in the class report | AI assumption |
| D07 | Implementation | `Cabin.changeMode()` takes no parameter, so the target mode is not given | Switches HOME ⇄ AWAY | Team Guide §6 |
| D08 | Implementation | What `Sensor.monitor()` does is not specified | Detects the condition only while the sensor is enabled | Team Guide §4 |
| D09 | Implementation | The guard `contactsConfigured` needs Incident to know the owner's contacts, but the class diagram gives Incident only a dependency on EmergencyContact | The guard returns `false` | AI assumption |
| D10 | Implementation | What `MonitoringSystem.evaluateEvent()` does is not specified | Calls `monitor()` on every sensor, then `createIncident()` and `escalateIncident()` as the sequence diagram shows. Every event is treated as Critical smoke (mock-up) | AI assumption |
| D11 | Sequence diagram | The lifelines *Communication Service* and *Emergency Service* are not classes in the class diagram | Left out of the verified scenario. They are external systems, and the delivery they do is simulated | Team Guide §16, §17 |
| D12 | Sequence diagram | The messages are prose, not method names | Each one mapped to a class diagram method (`evaluateEvent`, `createIncident`, `registerIncident`, `escalateIncident`, `receiveNotification`, `updateIncident`) | Team Guide §7, §9, §12 |
| D13 | Sequence diagram | *Register* and *Update Incident/Event History* are drawn as MonitoringSystem self-messages, but the class diagram puts these methods on `IncidentHistory` | `IncidentHistory` lifeline added, and the calls go to it | Team Guide §9 |
| D14 | Sequence and class diagram | The sequence has MonitoringSystem call IncidentHistory and EmergencyContact, but the class diagram has no relation from MonitoringSystem to either class | The implementation adds the two associations it needs (`history`, `contacts`). They show as Extra in the class report until the team decides | AI assumption |
| D15 | Sequence and class diagram | *Send / Deliver Critical Notification* to the owner, but `HytteOwner` has no method to receive a notification | Message left out of the scenario | AI assumption |
| D16 | State machine, System Operation page | The mode arrows (*owner selects HOME / AWAY*) have no action, so it is not clear how the class diagram's `Cabin.mode` attribute follows the state | Each arrow that changes the mode has the action `/ changeMode` (which switches HOME ⇄ AWAY, D07). `Awaiting → Home` has none, because `mode` starts as HOME | Team Guide §6 |
| D17 | State machine, System Operation page | The door and motion rule is only a note on the AWAY state (*Enabled Door/Motion monitoring can create security Warnings*), not a transition | Self-transitions `doorOpened` and `motionDetected / reportSecurityWarning` on `Away` and `AwayCold`; none on HOME, where they are ignored. The *Enabled* condition is not modelled, because no class holds per-sensor enabling for the owner | Team Guide §6 |

## Findings and team decisions

Findings are gaps or contradictions in the input set that need a **team
decision** rather than a deviation. Decisions made here change the verifier
input in `project/diagrams/conversion/`. **The team must make the same
change by hand in `model/`**, so the ground truth stays the source.

| ID | Finding | Decision | Status |
|----|---------|----------|--------|
| F01 | The firmware must show the Incident state on the LEDs, but the class diagram has no way to read it | Add `+state() State` to `Incident` (decided by the user, 2026-10-27) | Done in the conversion. **Team: add it to `model/class-diagram`** |
| F02 | The rule "a door in AWAY creates a Warning" is only on the *System Operation* state machine page, which was not converted | Convert the page (decided by the user, 2026-10-27): `state-cabin`, `state-monitoring_system` | Done. **Team: review the split and D16, D17** |
| F03 | In `state-cabin`, the Cabin reports a security Warning, but the class diagram gives Cabin no link to `MonitoringSystem` or `Incident`, so no Incident can be created from it | Open. Options: an association `Cabin → MonitoringSystem`, or MonitoringSystem reads `Cabin.state()` when it evaluates a door event | **Open, blocks the button A demo** |
| F04 | The LEDs must also show HOME / AWAY, and `Cabin` has the same gap as F01 | `+state() State` added to `Cabin` together with F02, following the same decision as F01 | Done in the conversion. **User to confirm; team: add it to `model/class-diagram`** |
| F05 | The class diagram does not show the state machine members of Incident, Cabin and MonitoringSystem (`state`, `handle()`, guards, actions): 17 Extra in the class report | Open: add them to the class diagram, as the template's examples do | Open |
| F06 | Sequence vs class diagram: MonitoringSystem calls IncidentHistory and EmergencyContact without a relation (D14): 2 Extra | Open | Open |
| F07 | `Incident ..> EmergencyContact` is drawn, but no Incident method uses EmergencyContact: 1 Missing | Open | Open |
| F08 | The sensor subclasses must override `detectCondition()` (D06), which they do not show: 8 Extra | Open | Open |
| F09 | ADR-001 is not testable: the class diagram has no way to disable a sensor and no thresholds | Open | Open |
