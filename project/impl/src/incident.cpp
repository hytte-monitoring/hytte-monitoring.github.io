#include "hytte/incident.hpp"

#include <utility>

namespace hytte {

#if __cplusplus < 201703L
// Before C++17 a static constexpr array that is used needs one definition outside the
// class. The micro:bit's CODAL build compiles with -std=c++11 (Phase 4).
constexpr Incident::Transition Incident::transitions[];
#endif

Incident::Incident(std::string incidentId, std::string timestamp, Severity severity,
                   std::vector<std::weak_ptr<EmergencyContact>> contacts)
    : incidentId_(std::move(incidentId)), severity_(severity), timestamp_(std::move(timestamp)),
      contacts_(std::move(contacts))
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

std::string Incident::getId() const { return incidentId_; }

Severity Incident::getSeverity() const { return severity_; }

// The design gives Incident no link to the owner's contacts, so it cannot know.
// At least one of the owner's contacts still exists (Team Guide §10, team decision on D09).
bool Incident::contactsConfigured() const
{
    for (const std::weak_ptr<EmergencyContact>& contact : contacts_)
    {
        if (!contact.expired())
        {
            return true;
        }
    }
    return false;
}

void Incident::notifyOwner() {}

void Incident::notifyContacts()
{
    for (const std::weak_ptr<EmergencyContact>& contact : contacts_)
    {
        if (auto c = contact.lock())
        {
            c->receiveNotification();
        }
    }
}

void Incident::contactEmergencyService() {}

}  // namespace hytte
