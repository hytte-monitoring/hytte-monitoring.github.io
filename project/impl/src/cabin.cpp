#include "hytte/cabin.hpp"

#include <utility>

namespace hytte {

Cabin::Cabin(std::string cabinId, std::string name) : cabinId_(std::move(cabinId)), name_(std::move(name)) {}

void Cabin::changeMode()
{
    mode_ = mode_ == MonitoringMode::HOME ? MonitoringMode::AWAY : MonitoringMode::HOME;
}

}  // namespace hytte
