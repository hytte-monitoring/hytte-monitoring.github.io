#include "hytte/monitoring_system.hpp"

#include <utility>

namespace hytte {

MonitoringSystem::MonitoringSystem(Cabin& cabin, IncidentHistory& history, std::vector<std::weak_ptr<EmergencyContact>> contacts)
    : cabin_(&cabin), history_(&history), contacts_(std::move(contacts))
{
    cabin.system_ = this;   // Cabin --> "1" MonitoringSystem
}

// Mock-up: every evaluated event is treated as Critical smoke (sequence-smoke_escalation).
void MonitoringSystem::evaluateEvent()
{
    for (const std::weak_ptr<Sensor>& sensor : sensors_)
    {
        if (auto s = sensor.lock())
        {
            s->monitor();
        }
    }
    createIncident();
    escalateIncident();
}

void MonitoringSystem::createIncident() { history_->registerIncident(); }

// The owner did not respond in time, so the contacts are notified (Team Guide §12).
void MonitoringSystem::escalateIncident()
{
    for (const std::weak_ptr<EmergencyContact>& contact : contacts_)
    {
        if (auto c = contact.lock())
        {
            c->receiveNotification();
        }
    }
    history_->updateIncident();
}

void MonitoringSystem::handle(Event event)
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

// Resilient monitoring (ADR-002): battery when cabin power fails,
// Cellular/SIM when the Internet fails, and back when they return.
void MonitoringSystem::useBatteryBackup() { onBatteryBackup_ = true; }

void MonitoringSystem::useCabinElectricity() { onBatteryBackup_ = false; }

void MonitoringSystem::useCellular() { cellularFallback_ = true; }

void MonitoringSystem::useInternet() { cellularFallback_ = false; }

}  // namespace hytte
