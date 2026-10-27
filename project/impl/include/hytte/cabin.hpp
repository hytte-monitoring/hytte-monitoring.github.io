#pragma once

#include <string>
#include <memory>
#include <vector>

#include "hytte/monitoring_mode.hpp"
#include "hytte/sensor.hpp"

namespace hytte {

class Cabin
{
public:
    Cabin(std::string cabinId, std::string name);

    void changeMode();

private:
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    std::string cabinId_;
    std::string name_;
    MonitoringMode mode_ = MonitoringMode::HOME;
    bool coldProtectionActive_ = false;
    std::vector<std::weak_ptr<Sensor>> sensors_;
};

}  // namespace hytte
