#pragma once

#include <string>
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
    std::string cabinId_;
    std::string name_;
    MonitoringMode mode_ = MonitoringMode::HOME;
    bool coldProtectionActive_ = false;
    std::vector<Sensor*> sensors_;
};

}  // namespace hytte
