#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class OutdoorTemperatureSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void readTemperature();

private:
    float temperature_ = 0.0f;
};

}  // namespace hytte
