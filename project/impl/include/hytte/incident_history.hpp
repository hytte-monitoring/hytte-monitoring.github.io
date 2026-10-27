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
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    // IncidentHistory *-- "*" Incident: the history owns every Incident (finding F10).
    std::vector<std::unique_ptr<Incident>> incidents_;
};

}  // namespace hytte
