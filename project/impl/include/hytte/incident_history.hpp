#pragma once

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
    std::vector<Incident*> incidents_;
};

}  // namespace hytte
