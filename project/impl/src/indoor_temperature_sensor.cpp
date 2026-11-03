#include "hytte/indoor_temperature_sensor.hpp"

namespace hytte {

void IndoorTemperatureSensor::detectCondition() { readTemperature(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void IndoorTemperatureSensor::readTemperature() {}

}  // namespace hytte
