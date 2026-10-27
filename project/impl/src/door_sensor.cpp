#include "hytte/door_sensor.hpp"

namespace hytte {

void DoorSensor::detectCondition() { detectDoorState(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void DoorSensor::detectDoorState() {}

}  // namespace hytte
