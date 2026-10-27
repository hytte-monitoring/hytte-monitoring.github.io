#include "hytte/connection_sensor.hpp"

namespace hytte {

void ConnectionSensor::detectCondition() { detectConnection(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void ConnectionSensor::detectConnection() {}

}  // namespace hytte
