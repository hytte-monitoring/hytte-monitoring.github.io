#include "hytte/monitoring_system.hpp"

namespace hytte {

MonitoringSystem::MonitoringSystem(Cabin& cabin) : cabin_(&cabin) {}

void MonitoringSystem::evaluateEvent()
{
    for (Sensor* sensor : sensors_)
    {
        sensor->monitor();
    }
}

void MonitoringSystem::createIncident() {}

void MonitoringSystem::escalateIncident() {}

}  // namespace hytte
