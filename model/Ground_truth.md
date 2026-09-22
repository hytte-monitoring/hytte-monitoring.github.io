# Hytte Monitoring – Ground Truth

## 1. System Concept

Hytte Monitoring is a simulated monitoring system for cabins.

The system allows a cabin owner to monitor important safety, security,
environmental, and system conditions while at home or away.

The delivered website is a static mock-up.

Real sensors, backend services, phone calls, SMS messages, cellular
communication, and emergency-service integrations are not implemented.

However, the UML models describe the conceptual system as if these
components and services exist.

---

## 2. Main User

The main user is the Hytte Owner/User.

The user can:

- Log in using a simulated Guest Login.
- Configure monitoring.
- Select optional monitoring functions.
- Configure allowed detection/notification levels.
- Change between HOME and AWAY mode.
- View the Monitoring Dashboard.
- View active Incidents.
- Mark Incidents as Resolved or Not Resolved.
- Request Suggested Next Steps.
- View Incident/Event History.
- Configure Family/Emergency Contacts.
- Configure automatic emergency escalation.

---

## 3. Supported Monitoring

The system supports:

- Smoke
- Indoor Temperature
- Outdoor Temperature
- Water Leak
- Door
- Motion
- Power
- Internet/Connection

The following are NOT included:

- CO sensor
- Camera

The Outdoor Temperature Sensor has a special system role.

It is used by the system to determine when cold-weather protection
must be activated.

---

## 4. Monitoring Configuration

Some monitoring functions are mandatory while others can be configured
by the user.

### Always Mandatory

The following monitoring is mandatory at all times:

- Smoke
- Internet/Connection

The user cannot disable these monitoring functions.

### Cold-Weather Monitoring

The system uses an Outdoor Temperature Sensor to determine when
cold-weather protection is required.

When the outside temperature reaches a system-defined cold-weather
threshold:

- Indoor Temperature monitoring becomes mandatory.
- Power monitoring becomes mandatory.

The user cannot disable Indoor Temperature or Power monitoring while
cold-weather protection is active.

The cold-weather threshold is controlled by the system and cannot be
changed by the user.

When cold-weather protection is not active, Indoor Temperature and
Power monitoring can be configured by the user.

### Optional Monitoring

The user can normally enable or disable:

- Water Leak
- Door
- Motion

---

## 5. Detection and Notification Levels

The user can configure detection/notification levels where appropriate.

The user can only make changes within an allowed safe range.

Critical thresholds are controlled by the system.

The user cannot disable or weaken a Critical threshold.

If an event reaches a Critical level, the system can notify the user
regardless of the user's normal notification preferences.

System-controlled safety thresholds have priority over normal
user configuration.

---

## 6. Monitoring Modes

The system has two monitoring modes:

- HOME
- AWAY

### HOME Mode

When the cabin is in HOME mode:

- Opening a door is normally allowed.
- Motion inside the cabin is normally allowed.

Door and Motion monitoring should therefore not normally create
security Warnings simply because activity is detected.

### AWAY Mode

When the cabin is in AWAY mode:

- Door activity can generate a Warning.
- Motion can generate a Warning.

### Monitoring Independent of HOME/AWAY

Safety, environmental, and system monitoring continue in both modes.

This includes:

- Smoke
- Indoor Temperature
- Outdoor Temperature
- Water Leak
- Power
- Internet/Connection

HOME/AWAY therefore mainly affects security-related behavior such as
Door and Motion detection.

---

## 7. Incidents

When the system detects a condition that requires attention,
it can create an Incident.

An Incident has one of two severity levels:

- Warning
- Critical

A Warning represents a condition that requires attention but is not
currently considered an immediate critical emergency.

A Critical Incident represents a serious condition that requires
immediate attention.

The user is notified when an Incident requires their attention.

Critical Incidents must notify the user immediately.

---

## 8. Incident Handling

After receiving an Incident, the user can choose:

- Resolved
- Not Resolved

### Resolved

If the user selects Resolved:

1. The Incident is closed.
2. The Incident is stored in Incident/Event History.

### Not Resolved

If the user selects Not Resolved:

1. The system asks whether the user wants Suggested Next Steps.
2. If the user selects Yes, the system displays step-by-step guidance.
3. The system asks again whether the Incident has been resolved.
4. If the Incident is resolved, it is closed and stored in History.
5. If it is still unresolved, the Incident remains Active.

If the user does not want Suggested Next Steps, the Incident remains
Active.

An Active Incident can later be marked as Resolved by the user.

---

## 9. Incident/Event History

All Warning and Critical Incidents are stored in Incident/Event History.

The history allows the user to view previous Incidents and their status.

This includes Incidents that were resolved by the user after receiving
guidance or escalation.

---

## 10. Escalation

The system uses escalation when an Incident is not handled by the user.

The preferred escalation order is:

1. Notify the Hytte Owner/User.
2. If there is no response, notify configured Family/Emergency Contacts.
3. If the situation remains unresolved and requires emergency assistance,
   the system can contact the relevant Emergency Service.

Human response is preferred before automatic contact with an Emergency
Service when the situation allows it.

The system determines the waiting/response time based on the severity
of the Incident.

The user does not configure this waiting time.

Critical situations can therefore have a shorter response time than
Warnings.

---

## 11. Warning Escalation

A Warning is first sent to the Hytte Owner/User.

If the user does not respond, the Warning can be escalated to configured
Family/Emergency Contacts.

A Warning does NOT automatically contact an official Emergency Service.

Example:

Warning
→ User
→ No response
→ Family/Emergency Contact

---

## 12. Critical Escalation

A Critical Incident must immediately notify the Hytte Owner/User.

If the user does not respond, the normal escalation path is:

User
→ Family/Emergency Contact
→ Relevant Emergency Service

Human intervention is preferred before automatic Emergency Service
contact when the situation allows it.

However, immediate critical danger can override normal escalation
restrictions and waiting periods.

For example, a serious fire can cause the system to contact the relevant
Emergency Service even when normal user configuration would otherwise
prevent automatic escalation.

Safety-critical behavior therefore has priority over normal user
preferences.

---

## 13. Emergency Contacts

The user can configure Family/Emergency Contacts.

These are trusted people who can receive notifications when the user
does not respond to an Incident.

Examples include:

- Family member
- Trusted person

Family/Emergency Contacts are different from official Emergency Services.

Emergency Services represent services such as:

- Fire department
- Police
- Other relevant emergency service

---

## 14. Power and Communication Reliability

The monitoring system is conceptually designed to continue operating
when normal cabin infrastructure fails.

During normal operation, the system can use:

- Cabin electricity
- Normal Internet connection

If normal cabin electricity fails:

- The monitoring system can switch to battery backup.

If normal Internet connectivity fails:

- The monitoring system can use Cellular/SIM communication as a fallback.

If both normal power and Internet connectivity fail:

- Battery backup can keep the monitoring system operating.
- Cellular/SIM communication can allow important notifications and
  communication to continue.

The current website only simulates this behavior.

No real battery, SIM, cellular network, phone call, or SMS integration
is implemented.

---

## 15. System-Controlled Safety Rules

Some system behavior cannot be overridden by the user.

These rules include:

- Smoke monitoring is mandatory at all times.
- Internet/Connection monitoring is mandatory at all times.
- Outdoor Temperature is monitored so the system can determine whether
  cold-weather protection is required.
- Indoor Temperature becomes mandatory during cold-weather conditions.
- Power monitoring becomes mandatory during cold-weather conditions.
- Critical thresholds are controlled by the system.
- Critical notifications cannot be suppressed by normal user preferences.
- Immediate critical danger can override normal escalation restrictions.

These rules exist to prevent normal configuration from disabling
safety-critical monitoring.

---

## 16. External Actors and Systems

The conceptual system can interact with the following external actors
or systems.

### Hytte Owner/User

The main user of Hytte Monitoring.

### Family/Emergency Contact

A trusted person who can receive notifications when the owner does not
respond.

### Emergency Service

Represents official services such as:

- Fire department
- Police
- Other relevant emergency services

### Communication Service

Represents the communication infrastructure used by Hytte Monitoring.

This can conceptually include:

- Internet communication
- Cellular/SIM communication
- Notifications
- Simulated emergency communication

There is no external Weather Service.

Cold-weather conditions are determined using the cabin's own
Outdoor Temperature Sensor.

---

## 17. Out of Scope

The following are outside the implementation scope:

- Real physical sensors
- Real backend infrastructure
- Real battery backup hardware
- Real SIM/cellular integration
- Real SMS messages
- Real phone calls
- Real Emergency Service communication
- Payment
- Billing
- Subscription management
- Camera monitoring
- CO monitoring
- External Weather Service integration

These interactions and components are simulated in the website where
necessary.

---

## 18. Architecture Decisions

### ADR-001 – Safety-Critical Monitoring Cannot Be Disabled

Safety-critical monitoring cannot be disabled or weakened by normal
user configuration.

This includes:

- Smoke monitoring being mandatory at all times.
- Internet/Connection monitoring being mandatory at all times.
- Indoor Temperature and Power becoming mandatory during cold-weather
  conditions.
- Critical thresholds being controlled by the system.
- Critical notifications overriding normal notification preferences.
- Immediate critical danger being able to override normal escalation
  restrictions.

The purpose is to prevent user configuration from making critical
safety functions ineffective.

### ADR-002 – Resilient Monitoring

The conceptual monitoring system should remain operational during
normal power or Internet failures.

The system conceptually uses:

- Battery backup during power failure.
- Cellular/SIM communication during normal Internet failure.

This allows monitoring and important communication to continue even
when normal cabin infrastructure is unavailable.

The static website only simulates this architecture.

---

## 19. UML Ground Truth Rules

The following five UML diagrams must describe this same system:

1. Use Case Diagram
2. Class Diagram
3. Activity Diagram
4. State Machine Diagram
5. Sequence Diagram

Each diagram represents a different view of Hytte Monitoring.

Team members must NOT independently:

- Add new system features.
- Remove agreed features.
- Change mandatory monitoring rules.
- Change Warning/Critical terminology.
- Change escalation behavior.
- Change the meaning of HOME/AWAY.
- Change cold-weather protection rules.
- Add Weather Service back into the system.
- Rename core concepts without group agreement.
- Introduce new external actors or systems without group agreement.

If something is unclear or missing, it must be discussed with the group
before the Ground Truth or UML model is changed.

The five UML diagrams are different views of the SAME Hytte Monitoring
system, not five independent system designs.
