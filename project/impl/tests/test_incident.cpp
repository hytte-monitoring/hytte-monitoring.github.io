// Unit tests for Incident: every transition of diagrams/input/state-incident.drawio,
// and the rules of Team Guide §7 and §8 that the transitions carry out.
#include "check.hpp"
#include "test_access.hpp"

using hytte::Incident;
using hytte::IncidentStatus;
using hytte::Severity;
using hytte::TestAccess;
using State = Incident::State;
using Event = Incident::Event;

namespace {

Incident incidentIn(State target)
{
    Severity severity = target == State::Critical ? Severity::CRITICAL : Severity::WARNING;
    Incident incident("I-1", "2026-10-27T12:00", severity);
    if (target == State::Warning)
    {
        incident.handle(Event::warningDetected);
    }
    if (target == State::Critical)
    {
        incident.handle(Event::criticalDetected);
    }
    return incident;
}

void startsInNew()
{
    Incident incident("I-1", "2026-10-27T12:00", Severity::WARNING);
    CHECK(incident.state() == State::New);
    CHECK(TestAccess::status(incident) == IncidentStatus::Active);
}

void newToWarning()
{
    Incident incident = incidentIn(State::New);
    incident.handle(Event::warningDetected);
    CHECK(incident.state() == State::Warning);
    CHECK(incident.getSeverity() == Severity::WARNING);
}

void newToCritical()
{
    Incident incident("I-1", "2026-10-27T12:00", Severity::CRITICAL);
    incident.handle(Event::criticalDetected);
    CHECK(incident.state() == State::Critical);
    CHECK(incident.getSeverity() == Severity::CRITICAL);
}

// Team Guide §7: the SAME Incident is upgraded; no new Incident is created.
void warningUpgradesSameIncidentToCritical()
{
    Incident incident = incidentIn(State::Warning);
    incident.handle(Event::conditionWorsens);
    CHECK(incident.state() == State::Critical);
    CHECK(incident.getSeverity() == Severity::CRITICAL);
    CHECK(incident.getId() == "I-1");
    CHECK(TestAccess::status(incident) == IncidentStatus::Active);
}

// Team Guide §8: Resolved closes the Incident.
void resolveClosesFromWarningAndCritical()
{
    for (State from : {State::Warning, State::Critical})
    {
        Incident incident = incidentIn(from);
        incident.handle(Event::ownerResolved);
        CHECK(incident.state() == State::Closed);
        CHECK(TestAccess::status(incident) == IncidentStatus::Closed);
    }
}

// Escalation transitions loop back to the same state (Critical stays Critical).
void escalationKeepsCritical()
{
    for (Event event : {Event::ownerWaitingTimeout, Event::contactWaitingTimeout, Event::safetyOverride})
    {
        Incident incident = incidentIn(State::Critical);
        incident.handle(event);
        CHECK(incident.state() == State::Critical);
    }
}

// Team Guide §11: a Warning does NOT contact the Emergency Service.
void warningIgnoresEmergencyEscalation()
{
    for (Event event : {Event::contactWaitingTimeout, Event::safetyOverride})
    {
        Incident incident = incidentIn(State::Warning);
        incident.handle(event);
        CHECK(incident.state() == State::Warning);
        CHECK(incident.getSeverity() == Severity::WARNING);
    }
}

// Events without an arrow in the diagram are ignored.
void eventsWithoutTransitionAreIgnored()
{
    Incident fresh = incidentIn(State::New);
    fresh.handle(Event::ownerResolved);
    CHECK(fresh.state() == State::New);

    Incident critical = incidentIn(State::Critical);
    critical.handle(Event::conditionWorsens);
    CHECK(critical.state() == State::Critical);

    Incident closed = incidentIn(State::Warning);
    closed.handle(Event::ownerResolved);
    closed.handle(Event::criticalDetected);
    closed.handle(Event::conditionWorsens);
    CHECK(closed.state() == State::Closed);
}

}  // namespace

int main()
{
    startsInNew();
    newToWarning();
    newToCritical();
    warningUpgradesSameIncidentToCritical();
    resolveClosesFromWarningAndCritical();
    escalationKeepsCritical();
    warningIgnoresEmergencyEscalation();
    eventsWithoutTransitionAreIgnored();
    return test::finish("test_incident");
}
