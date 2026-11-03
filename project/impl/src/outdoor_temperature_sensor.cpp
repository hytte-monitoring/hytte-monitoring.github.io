#include "hytte/outdoor_temperature_sensor.hpp"

namespace hytte {

void OutdoorTemperatureSensor::detectCondition() { readTemperature(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void OutdoorTemperatureSensor::readTemperature() {}

}  // namespace hytte
