#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class DoorSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectDoorState();

private:
    bool open_ = false;
};

}  // namespace hytte
