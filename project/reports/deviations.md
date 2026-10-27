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
| Team Guide | 7 |
| AI assumption, open for the team | 8 |
| **Total** | **15** |

| ID | Where | Unclear in the UML or ADR | Resolution | Source |
|----|-------|---------------------------|------------|--------|
| D01 | Class diagram | The 8 lines between classes have no arrowheads, so it is not clear which class refers to which | Owner → owned or used: Owner → Cabin, Contact and Incident; Cabin → Sensor; System → Cabin, Sensor and Incident; History → Incident | Team Guide §1, §2, §3, §7, §9, §13 |
| D02 | Class diagram | The 8 associations have no role names, but in C++ each one is a named member | Named after the target class (`cabins`, `contacts`, `incidents`, `sensors`, `cabin`) | AI assumption |
| D03 | Class diagram | HytteOwner–EmergencyContact and HytteOwner–Incident have no multiplicity | `*` for both: the owner configures contacts (plural) and views and resolves Incidents | Team Guide §2, §8, §13 |
| D04 | Class diagram | MonitoringSystem–Cabin has no multiplicity | `1`: one monitoring system per cabin | AI assumption |
| D05 | Class diagram | `Incident.timestamp` has type `DateTime`, which is not defined anywhere | `string` | AI assumption |
| D06 | Class diagram | `Sensor` is `<<abstract>>` but has no abstract method, which C++ requires | `detectCondition()` made abstract: each subclass has its own detection | AI assumption |
| D07 | Implementation | `Cabin.changeMode()` takes no parameter, so the target mode is not given | Switches HOME ⇄ AWAY | Team Guide §6 |
| D08 | Implementation | What `Sensor.monitor()` does is not specified | Detects the condition only while the sensor is enabled | Team Guide §4 |
| D09 | Implementation | The guard `contactsConfigured` needs Incident to know the owner's contacts, but the class diagram gives Incident only a dependency on EmergencyContact | The guard returns `false` | AI assumption |
| D10 | Implementation | What `MonitoringSystem.evaluateEvent()` does is not specified | Calls `monitor()` on every sensor | AI assumption |
| D11 | Sequence diagram | The lifelines *Communication Service* and *Emergency Service* are not classes in the class diagram | Left out of the verified scenario. They are external systems, and the delivery they do is simulated | Team Guide §16, §17 |
| D12 | Sequence diagram | The messages are prose, not method names | Each one mapped to a class diagram method (`evaluateEvent`, `createIncident`, `registerIncident`, `escalateIncident`, `receiveNotification`, `updateIncident`) | Team Guide §7, §9, §12 |
| D13 | Sequence diagram | *Register* and *Update Incident/Event History* are drawn as MonitoringSystem self-messages, but the class diagram puts these methods on `IncidentHistory` | `IncidentHistory` lifeline added, and the calls go to it | Team Guide §9 |
| D14 | Sequence and class diagram | The sequence has MonitoringSystem call IncidentHistory and EmergencyContact, but the class diagram has no relation from MonitoringSystem to either class | The implementation adds the two associations it needs (`history`, `contacts`). They show as Extra in the class report until the team decides | AI assumption |
| D15 | Sequence and class diagram | *Send / Deliver Critical Notification* to the owner, but `HytteOwner` has no method to receive a notification | Message left out of the scenario | AI assumption |
