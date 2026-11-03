#include "hytte/sensor.hpp"

#include <utility>

namespace hytte {

Sensor::Sensor(std::string sensorID) : sensorID_(std::move(sensorID)) {}

void Sensor::monitor()
{
    if (enabled_)
    {
        detectCondition();
    }
}

}  // namespace hytte
