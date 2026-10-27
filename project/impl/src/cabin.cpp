#include "hytte/cabin.hpp"

#include "hytte/monitoring_system.hpp"

#include <utility>

namespace hytte {

#if __cplusplus < 201703L
// Before C++17 a static constexpr array that is used needs one definition outside the
// class. The micro:bit's CODAL build compiles with -std=c++11 (Phase 4).
constexpr Cabin::Transition Cabin::transitions[];
#endif

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

// Door or motion in AWAY: the system creates an Incident (Team Guide §6, §7; finding F03).
void Cabin::reportSecurityWarning()
{
    if (system_ != nullptr)
    {
        system_->createIncident(Severity::WARNING);
    }
}

}  // namespace hytte
