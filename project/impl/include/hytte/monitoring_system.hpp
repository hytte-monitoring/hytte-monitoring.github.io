#pragma once

#include <vector>

#include "hytte/cabin.hpp"
#include "hytte/incident.hpp"
#include "hytte/sensor.hpp"

namespace hytte {

class MonitoringSystem
{
public:
    explicit MonitoringSystem(Cabin& cabin);

    void evaluateEvent();
    void createIncident();
    void escalateIncident();

private:
    bool onBatteryBackup_ = false;
    bool cellularFallback_ = false;
    Cabin* cabin_;
    std::vector<Sensor*> sensors_;
    std::vector<Incident*> incidents_;
};

}  // namespace hytte
