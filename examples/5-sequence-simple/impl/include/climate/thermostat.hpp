#pragma once

#include "climate/heater.hpp"
#include "climate/sensor.hpp"

namespace climate {

class Thermostat
{
public:
    Thermostat(Sensor& sensor, Heater& heater);

    void setTarget(double celsius);

private:
    Sensor& sensor_;   // reference -> association: the thermostat refers to its sensor
    Heater& heater_;   // reference -> association
    double target_ = 20.0;
};

}  // namespace climate
