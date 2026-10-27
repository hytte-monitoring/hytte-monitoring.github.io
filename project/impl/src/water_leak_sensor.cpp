#include "hytte/water_leak_sensor.hpp"

namespace hytte {

void WaterLeakSensor::detectCondition() { detectLeak(); }

// Mock-up: a real sensor reading is out of scope (Team Guide §17).
void WaterLeakSensor::detectLeak() {}

}  // namespace hytte
