#include "climate/thermostat.hpp"

namespace climate {

Thermostat::Thermostat(Sensor& sensor, Heater& heater) : sensor_(sensor), heater_(heater) {}

void Thermostat::setTarget(double celsius)
{
    target_ = celsius;
    const double reading = sensor_.read();
    if (reading < target_)
    {
        heater_.turnOn();
    }
    else
    {
        heater_.turnOff();
    }
}

}  // namespace climate
