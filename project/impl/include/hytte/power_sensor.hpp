#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class PowerSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectPowerState();

private:
    bool powerAvailable_ = true;
};

}  // namespace hytte
