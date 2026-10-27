#include "hytte/hytte_owner.hpp"

#include <utility>

namespace hytte {

HytteOwner::HytteOwner(std::string userID, std::string name, IncidentHistory& history)
    : userID_(std::move(userID)), name_(std::move(name)), history_(&history)
{
}

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

// The owner selects Resolved: the Incident is closed and its history record is
// updated (Team Guide §8, finding F15).
void HytteOwner::resolveIncident(const std::string& incidentId)
{
    Incident* incident = history_->findIncident(incidentId);
    if (incident == nullptr)
    {
        return;
    }
    incident->handle(Incident::Event::ownerResolved);
    history_->updateIncident();
}

}  // namespace hytte
