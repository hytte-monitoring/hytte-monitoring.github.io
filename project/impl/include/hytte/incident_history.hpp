#pragma once

#include <cstddef>
#include <memory>
#include <vector>

#include "hytte/incident.hpp"
#include "hytte/severity.hpp"

namespace hytte {

class IncidentHistory
{
public:
    void registerIncident(Severity severity);
    void updateIncident();
    std::vector<Incident> viewHistory() const;

private:
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    // The board keeps only the latest Incidents; the dashboard database keeps all (F13).
    std::size_t maxIncidents_ = 20;
    // IncidentHistory *-- "*" Incident: the history owns every Incident (finding F10).
    std::vector<std::unique_ptr<Incident>> incidents_;
};

}  // namespace hytte
