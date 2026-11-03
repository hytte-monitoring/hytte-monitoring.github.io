#include "climate/heater.hpp"

namespace climate {

void Heater::turnOn() { on_ = true; }

void Heater::turnOff() { on_ = false; }

bool Heater::isOn() const { return on_; }

}  // namespace climate
