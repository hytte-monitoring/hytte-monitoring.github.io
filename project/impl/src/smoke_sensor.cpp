#include "hytte/smoke_sensor.hpp"

namespace hytte {

void SmokeSensor::detectCondition() { detectSmoke(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void SmokeSensor::detectSmoke() {}

}  // namespace hytte
