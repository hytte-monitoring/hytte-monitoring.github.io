#include "climate/sensor.hpp"

namespace climate {

Sensor::Sensor(double reading) : reading_(reading) {}

double Sensor::read() const { return reading_; }

}  // namespace climate
