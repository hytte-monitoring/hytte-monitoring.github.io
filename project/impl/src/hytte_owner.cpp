#include "hytte/hytte_owner.hpp"

#include <utility>

namespace hytte {

HytteOwner::HytteOwner(std::string userID, std::string name) : userID_(std::move(userID)), name_(std::move(name)) {}

void HytteOwner::configureMonitoring() {}

void HytteOwner::changeMode()
{
    for (const std::weak_ptr<Cabin>& cabin : cabins_)
    {
        if (auto c = cabin.lock())
        {
            c->changeMode();
        }
    }
}

void HytteOwner::resolveIncident() {}

}  // namespace hytte
