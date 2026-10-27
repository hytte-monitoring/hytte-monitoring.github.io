#pragma once

#include <string>

#include "hytte/incident_status.hpp"
#include "hytte/severity.hpp"

namespace hytte {

class Incident
{
public:
    // The states and events of diagrams/input/state-incident.drawio.
    enum class State { New, Warning, Critical, Closed };
    enum class Event {
        warningDetected,
        criticalDetected,
        conditionWorsens,
        ownerWaitingTimeout,
        contactWaitingTimeout,
        safetyOverride,
        ownerResolved,
    };

    Incident(std::string incidentId, std::string timestamp);

    void upgradeToCritical();
    void resolve();

    void handle(Event event);
    State state() const;

private:
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    std::string incidentId_;
    Severity severity_ = Severity::WARNING;
    IncidentStatus status_ = IncidentStatus::Active;
    std::string timestamp_;
    State state_ = State::New;   // the initial state

    bool contactsConfigured() const;
    void notifyOwner();
    void notifyContacts();
    void contactEmergencyService();

    // The transition table: one row per arrow in the state diagram.
    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Incident::*guard)() const;   // nullptr: no guard
        void (Incident::*action)();        // nullptr: no action
    };
    static constexpr Transition transitions[] = {
        {State::New,      Event::warningDetected,       State::Warning,  nullptr, &Incident::notifyOwner},
        {State::New,      Event::criticalDetected,      State::Critical, nullptr, &Incident::notifyOwner},
        {State::Warning,  Event::conditionWorsens,      State::Critical, nullptr, &Incident::upgradeToCritical},
        {State::Warning,  Event::ownerWaitingTimeout,   State::Warning,  &Incident::contactsConfigured, &Incident::notifyContacts},
        {State::Critical, Event::ownerWaitingTimeout,   State::Critical, &Incident::contactsConfigured, &Incident::notifyContacts},
        {State::Critical, Event::contactWaitingTimeout, State::Critical, nullptr, &Incident::contactEmergencyService},
        {State::Critical, Event::safetyOverride,        State::Critical, nullptr, &Incident::contactEmergencyService},
        {State::Warning,  Event::ownerResolved,         State::Closed,   nullptr, &Incident::resolve},
        {State::Critical, Event::ownerResolved,         State::Closed,   nullptr, &Incident::resolve},
    };
};

}  // namespace hytte
