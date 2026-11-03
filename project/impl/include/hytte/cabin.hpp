#pragma once

#include <memory>
#include <string>
#include <vector>

#include "hytte/monitoring_mode.hpp"
#include "hytte/sensor.hpp"

namespace hytte {

class MonitoringSystem;

class Cabin
{
public:
    // The states and events of diagrams/input/state-cabin.drawio: the monitoring mode
    // and the cold-weather protection of the System Operation page, flattened.
    enum class State { Awaiting, Home, Away, AwaitingCold, HomeCold, AwayCold };
    enum class Event { ownerSelectsHome, ownerSelectsAway, coldRequired, coldGone, doorOpened, motionDetected };

    Cabin(std::string cabinId, std::string name);

    void changeMode();
    void handle(Event event);
    State state() const;

private:
    friend struct TestAccess;      // lets the unit tests read private state; not a UML element
    friend class MonitoringSystem; // links itself to its Cabin on construction (finding F03)

    std::string cabinId_;
    std::string name_;
    MonitoringMode mode_ = MonitoringMode::HOME;
    bool coldProtectionActive_ = false;
    std::vector<std::weak_ptr<Sensor>> sensors_;
    MonitoringSystem* system_ = nullptr;
    State state_ = State::Awaiting;   // the initial state

    void activateColdProtection();
    void deactivateColdProtection();
    void reportSecurityWarning();

    // The transition table: one row per arrow in the state diagram.
    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Cabin::*guard)() const;   // nullptr: no guard
        void (Cabin::*action)();        // nullptr: no action
    };
    static constexpr Transition transitions[] = {
        {State::Awaiting,     Event::ownerSelectsHome, State::Home,         nullptr, nullptr},
        {State::Awaiting,     Event::ownerSelectsAway, State::Away,         nullptr, &Cabin::changeMode},
        {State::Home,         Event::ownerSelectsAway, State::Away,         nullptr, &Cabin::changeMode},
        {State::Away,         Event::ownerSelectsHome, State::Home,         nullptr, &Cabin::changeMode},
        {State::AwaitingCold, Event::ownerSelectsHome, State::HomeCold,     nullptr, nullptr},
        {State::AwaitingCold, Event::ownerSelectsAway, State::AwayCold,     nullptr, &Cabin::changeMode},
        {State::HomeCold,     Event::ownerSelectsAway, State::AwayCold,     nullptr, &Cabin::changeMode},
        {State::AwayCold,     Event::ownerSelectsHome, State::HomeCold,     nullptr, &Cabin::changeMode},
        {State::Awaiting,     Event::coldRequired,     State::AwaitingCold, nullptr, &Cabin::activateColdProtection},
        {State::Home,         Event::coldRequired,     State::HomeCold,     nullptr, &Cabin::activateColdProtection},
        {State::Away,         Event::coldRequired,     State::AwayCold,     nullptr, &Cabin::activateColdProtection},
        {State::AwaitingCold, Event::coldGone,         State::Awaiting,     nullptr, &Cabin::deactivateColdProtection},
        {State::HomeCold,     Event::coldGone,         State::Home,         nullptr, &Cabin::deactivateColdProtection},
        {State::AwayCold,     Event::coldGone,         State::Away,         nullptr, &Cabin::deactivateColdProtection},
        {State::Away,         Event::doorOpened,       State::Away,         nullptr, &Cabin::reportSecurityWarning},
        {State::Away,         Event::motionDetected,   State::Away,         nullptr, &Cabin::reportSecurityWarning},
        {State::AwayCold,     Event::doorOpened,       State::AwayCold,     nullptr, &Cabin::reportSecurityWarning},
        {State::AwayCold,     Event::motionDetected,   State::AwayCold,     nullptr, &Cabin::reportSecurityWarning},
    };
};

}  // namespace hytte
