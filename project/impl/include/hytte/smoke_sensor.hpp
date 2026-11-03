#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class SmokeSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectSmoke();

private:
    bool smokeDetected_ = false;
};

}  // namespace hytte
