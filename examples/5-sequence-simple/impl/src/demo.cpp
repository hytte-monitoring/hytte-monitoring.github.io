#include <iostream>

#include "climate/thermostat.hpp"

int main()
{
    climate::Sensor sensor(18.5);
    climate::Heater heater;
    climate::Thermostat thermostat(sensor, heater);

    thermostat.setTarget(21.0);
    std::cout << "target 21.0, reading " << sensor.read() << ": heater "
              << (heater.isOn() ? "on" : "off") << "\n";
    thermostat.setTarget(16.0);
    std::cout << "target 16.0, reading " << sensor.read() << ": heater "
              << (heater.isOn() ? "on" : "off") << "\n";
    return 0;
}
