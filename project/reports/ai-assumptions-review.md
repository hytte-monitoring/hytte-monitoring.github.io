# AI assumptions: team review

In this project an **AI assumption is not a solution**. When the diagrams and the
Team Guide did not settle a question, the AI made the smallest assumption it could,
so the work could go on. Each one stays **open** until the team decides
([CLAUDE.md](../../CLAUDE.md#deviations)). The full log is in
[deviations.md](deviations.md).

There were **13 open AI assumptions** at FoM point 9. **The team reviewed all 13 on
2026-10-27** (FoM point 10): it kept 10 and changed 3 (D09, D14, D15). None is open now.

## How to review

For each item, tick one box and add a short note if needed:

- **Keep**: the team agrees with the AI's choice.
- **Change to …**: the team wants something else (write what).
- **Settled by Team Guide §…**: the Team Guide already answers it (write the section).

Then give the answers to the AI. Each one is logged as a **team decision** in
`deviations.md`. A "change" is applied to the official model or the code, the
verifier is run, and a new FoM point is added. The "AI assumption, open" line in
the chart (`fom.png`) goes down as items are decided.

---

## A. Small technical details the C++ needed (low risk)

### D02 – Names of the lines in the class diagram
- **Unclear:** the 8 lines between classes have no names, but in C++ each line is a named member.
- **AI chose:** named after the class they point to: `cabins`, `contacts`, `incidents`, `sensors`, `cabin`.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D18 – The Cabin → MonitoringSystem line (your decision F03)
- **Unclear:** the line has no name or number.
- **AI chose:** name `system`, number `1` (one cabin, one monitoring system).
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D24 – The HytteOwner → IncidentHistory line (decision F15)
- **Unclear:** the line has no name or number.
- **AI chose:** name `history`, number `1`.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D05 – The type `DateTime`
- **Unclear:** `Incident.timestamp` is a `DateTime`, which is not defined anywhere.
- **AI chose:** `string`. The micro:bit has no clock, so it stays empty for now.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D21 – Ids for new Incidents (decision F10)
- **Unclear:** nothing in the design gives a new Incident its id.
- **AI chose:** `I-1`, `I-2`, … in order, never reused. They start again at `I-1` after a reset.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D25 – Resolving an Incident that does not exist (decision F15)
- **Unclear:** what happens when the owner resolves an id that is not on the board (for example one dropped by the limit of 20).
- **AI chose:** nothing happens.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

---

## B. Choices that change behaviour (worth a real decision)

### D04 – How many cabins one monitoring system watches
- **Unclear:** the MonitoringSystem–Cabin line has no number.
- **AI chose:** `1`.
- **Hint:** Team Guide §1 speaks of "cabins", plural. Is that one system per cabin, or one for several?
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D06 – `Sensor` is abstract but has no abstract method
- **Unclear:** in C++ an abstract class needs at least one abstract method.
- **AI chose:** made `detectCondition()` abstract.
- **Effect:** every sensor must then repeat `detectCondition()`, which shows as 8 "extra" methods in the class report.
- **Options:** keep; draw `detectCondition()` on each sensor in the class diagram; or make `Sensor` a normal class.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D09 – The guard "contacts configured"
- **Unclear:** the Incident state machine checks whether contacts are configured, but an Incident has no link to the contacts.
- **AI chose:** the check always says **no**.
- **Effect:** **escalation to family contacts never happens** in the state machine.
- **Hint:** Team Guide §10–§12 describe escalation to contacts in detail.
- [ ] Keep  [x] Change to: escalation must be possible. `Incident --> "*" EmergencyContact : contacts`; the system gives each new Incident its contacts  [ ] Settled by Team Guide §____

### D10 – What `evaluateEvent()` does
- **Unclear:** the design does not say.
- **AI chose:** it checks the sensors, then treats the event as **Critical smoke** (the `smoke_escalation` sequence).
- **Effect:** fine for the demo, but it is not general. A door goes through Cabin instead.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____

### D14 – Calls with no line in the class diagram
- **Unclear:** the sequence diagram has MonitoringSystem call IncidentHistory and EmergencyContact, but the class diagram has no line between them.
- **AI chose:** added the two lines in the code only.
- **Effect:** 2 "extra" in the class report.
- **Options:** keep; add the two lines to the class diagram; or change the sequence diagram.
- [ ] Keep  [x] Change to: add the 2 lines to the class diagram  [ ] Settled by Team Guide §____

### D15 – The owner is not notified in the scenario
- **Unclear:** the sequence diagram sends a Critical notification to the owner, but `HytteOwner` has no method to receive it.
- **AI chose:** left that message out.
- **Hint:** Team Guide §7 says the user **is** notified when an Incident needs attention.
- [ ] Keep  [x] Change to: add `+receiveNotification() void` to HytteOwner (Team Guide §7); see finding F18  [ ] Settled by Team Guide §____

### D22 – Size of the history limit (decision F13)
- **Unclear:** the team decided on a limit, but not its size or what is dropped.
- **AI chose:** 20 Incidents on the board; when full, the oldest **closed** one goes first, otherwise the oldest. The browser database keeps everything.
- **Hint:** Team Guide §9 says all Incidents are stored. That is still true in the browser database.
- [x] Keep  [ ] Change to: ________  [ ] Settled by Team Guide §____
