#pragma once

#include <cstddef>
#include <string>
#include <memory>
#include <vector>

#include "hytte/emergency_contact.hpp"
#include "hytte/incident.hpp"
#include "hytte/severity.hpp"

namespace hytte {

class IncidentHistory
{
public:
    void registerIncident(Severity severity, const std::vector<std::weak_ptr<EmergencyContact>>& contacts);
    void updateIncident();
    std::vector<Incident> viewHistory() const;
    Incident* findIncident(const std::string& incidentId);

private:
    friend struct TestAccess;   // lets the unit tests read private state; not a UML element

    // The board keeps only the latest Incidents; the dashboard database keeps all (F13).
    std::size_t maxIncidents_ = 20;
    // IncidentHistory *-- "*" Incident: the history owns every Incident (finding F10).
    std::vector<std::unique_ptr<Incident>> incidents_;
};

}  // namespace hytte
