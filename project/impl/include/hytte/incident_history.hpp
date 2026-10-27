#pragma once

#include <memory>
#include <vector>

#include "hytte/incident.hpp"

namespace hytte {

class IncidentHistory
{
public:
    void registerIncident();
    void updateIncident();
    void viewHistory();

private:
    std::vector<std::weak_ptr<Incident>> incidents_;
};

}  // namespace hytte
