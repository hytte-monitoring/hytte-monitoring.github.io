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
    MonitoringSystem(Cabin& cabin, IncidentHistory& history, std::vector<std::weak_ptr<EmergencyContact>> contacts);

    void evaluateEvent();
    void createIncident();
    void escalateIncident();

private:
    bool onBatteryBackup_ = false;
    bool cellularFallback_ = false;
    Cabin* cabin_;
    std::vector<std::weak_ptr<Sensor>> sensors_;
    std::vector<std::weak_ptr<Incident>> incidents_;
    // Not in the class diagram: needed by sequence-smoke_escalation (deviation D14).
    IncidentHistory* history_;
    std::vector<std::weak_ptr<EmergencyContact>> contacts_;
};

}  // namespace hytte
