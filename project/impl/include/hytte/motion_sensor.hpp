#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class MotionSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectMotion();

private:
    bool motionDetected_ = false;
};

}  // namespace hytte
