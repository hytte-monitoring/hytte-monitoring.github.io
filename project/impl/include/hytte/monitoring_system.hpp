#pragma once

#include <memory>
#include <vector>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/sensor.hpp"

namespace hytte {

class MonitoringSystem
{
public:
    // The states and events of diagrams/input/state-monitoring_system.drawio: the power
    // source and the communication channel of the System Operation page, flattened.
    enum class State { ElectricityAndInternet, BatteryAndInternet, ElectricityAndCellular, BatteryAndCellular };
    enum class Event { powerLost, powerRestored, internetLost, internetRestored };

    MonitoringSystem(Cabin& cabin, IncidentHistory& history, std::vector<std::weak_ptr<EmergencyContact>> contacts);
    // The Cabin points back to this object, so it must not be copied.
    MonitoringSystem(const MonitoringSystem&) = delete;
    MonitoringSystem& operator=(const MonitoringSystem&) = delete;

    void evaluateEvent();
    void createIncident();
    void escalateIncident();
    void handle(Event event);

private:
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    bool onBatteryBackup_ = false;
    bool cellularFallback_ = false;
    Cabin* cabin_;
    std::vector<std::weak_ptr<Sensor>> sensors_;
    std::vector<std::weak_ptr<Incident>> incidents_;
    // Not in the class diagram: needed by sequence-smoke_escalation (deviation D14).
    IncidentHistory* history_;
    std::vector<std::weak_ptr<EmergencyContact>> contacts_;
    State state_ = State::ElectricityAndInternet;   // the initial state

    void useBatteryBackup();
    void useCabinElectricity();
    void useCellular();
    void useInternet();

    // The transition table: one row per arrow in the state diagram.
    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (MonitoringSystem::*guard)() const;   // nullptr: no guard
        void (MonitoringSystem::*action)();        // nullptr: no action
    };
    static constexpr Transition transitions[] = {
        {State::ElectricityAndInternet, Event::powerLost,        State::BatteryAndInternet,     nullptr, &MonitoringSystem::useBatteryBackup},
        {State::BatteryAndInternet,     Event::powerRestored,    State::ElectricityAndInternet, nullptr, &MonitoringSystem::useCabinElectricity},
        {State::ElectricityAndCellular, Event::powerLost,        State::BatteryAndCellular,     nullptr, &MonitoringSystem::useBatteryBackup},
        {State::BatteryAndCellular,     Event::powerRestored,    State::ElectricityAndCellular, nullptr, &MonitoringSystem::useCabinElectricity},
        {State::ElectricityAndInternet, Event::internetLost,     State::ElectricityAndCellular, nullptr, &MonitoringSystem::useCellular},
        {State::ElectricityAndCellular, Event::internetRestored, State::ElectricityAndInternet, nullptr, &MonitoringSystem::useInternet},
        {State::BatteryAndInternet,     Event::internetLost,     State::BatteryAndCellular,     nullptr, &MonitoringSystem::useCellular},
        {State::BatteryAndCellular,     Event::internetRestored, State::BatteryAndInternet,     nullptr, &MonitoringSystem::useInternet},
    };
};

}  // namespace hytte
