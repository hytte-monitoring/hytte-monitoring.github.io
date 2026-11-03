#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class WaterLeakSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectLeak();

private:
    bool leakDetected_ = false;
};

}  // namespace hytte
