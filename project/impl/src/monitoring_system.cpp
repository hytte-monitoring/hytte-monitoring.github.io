#include "hytte/monitoring_system.hpp"

#include <utility>

namespace hytte {

MonitoringSystem::MonitoringSystem(Cabin& cabin, IncidentHistory& history, std::vector<EmergencyContact*> contacts)
    : cabin_(&cabin), history_(&history), contacts_(std::move(contacts))
{
}

// Mock-up: every evaluated event is treated as Critical smoke (sequence-smoke_escalation).
void MonitoringSystem::evaluateEvent()
{
    for (Sensor* sensor : sensors_)
    {
        sensor->monitor();
    }
    createIncident();
    escalateIncident();
}

void MonitoringSystem::createIncident() { history_->registerIncident(); }

// The owner did not respond in time, so the contacts are notified (Team Guide §12).
void MonitoringSystem::escalateIncident()
{
    for (EmergencyContact* contact : contacts_)
    {
        contact->receiveNotification();
    }
    history_->updateIncident();
}

}  // namespace hytte
