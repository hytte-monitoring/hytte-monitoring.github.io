#include "hytte/incident.hpp"

#include <utility>

namespace hytte {

Incident::Incident(std::string incidentId, std::string timestamp)
    : incidentId_(std::move(incidentId)), timestamp_(std::move(timestamp))
{
}

// The SAME Incident is upgraded; no new Incident is created (Team Guide §7).
void Incident::upgradeToCritical() { severity_ = Severity::CRITICAL; }

void Incident::resolve() { status_ = IncidentStatus::Closed; }

void Incident::handle(Event event)
{
    for (const Transition& t : transitions)
    {
        if (t.from != state_ || t.event != event)
        {
            continue;
        }
        if (t.guard != nullptr && !(this->*t.guard)())
        {
            continue;
        }
        if (t.action != nullptr)
        {
            (this->*t.action)();
        }
        state_ = t.to;
        return;
    }
    // No transition for this event in this state: the event is ignored.
}

Incident::State Incident::state() const { return state_; }

// The design gives Incident no link to the owner's contacts, so it cannot know.
bool Incident::contactsConfigured() const { return false; }

void Incident::notifyOwner() {}

void Incident::notifyContacts() {}

void Incident::contactEmergencyService() {}

}  // namespace hytte
