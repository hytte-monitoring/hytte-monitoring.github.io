#include "hytte/power_sensor.hpp"

namespace hytte {

void PowerSensor::detectCondition() { detectPowerState(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void PowerSensor::detectPowerState() {}

}  // namespace hytte
