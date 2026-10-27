#include "hytte/cabin.hpp"

#include <utility>

namespace hytte {

Cabin::Cabin(std::string cabinId, std::string name) : cabinId_(std::move(cabinId)), name_(std::move(name)) {}

void Cabin::changeMode()
{
    mode_ = mode_ == MonitoringMode::HOME ? MonitoringMode::AWAY : MonitoringMode::HOME;
}

void Cabin::handle(Event event)
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
    // In HOME, door and motion events therefore create no Warning (Team Guide §6).
}

Cabin::State Cabin::state() const { return state_; }

// Indoor Temperature and Power become mandatory (Team Guide §4).
void Cabin::activateColdProtection() { coldProtectionActive_ = true; }

// The owner's previous choices are restored (Team Guide §4).
void Cabin::deactivateColdProtection() { coldProtectionActive_ = false; }

// Mock-up: the model has no link from Cabin to MonitoringSystem or Incident,
// so the Warning cannot be created from here (finding F03).
void Cabin::reportSecurityWarning() {}

}  // namespace hytte
