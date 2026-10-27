#pragma once

#include "hytte/sensor.hpp"

namespace hytte {

class ConnectionSensor : public Sensor
{
public:
    using Sensor::Sensor;

    void detectCondition() override;
    void detectConnection();

private:
    bool connected_ = true;
};

}  // namespace hytte
