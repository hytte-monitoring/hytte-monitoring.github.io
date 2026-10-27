#include "hytte/motion_sensor.hpp"

namespace hytte {

void MotionSensor::detectCondition() { detectMotion(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void MotionSensor::detectMotion() {}

}  // namespace hytte
