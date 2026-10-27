#include "hytte/incident_history.hpp"

#include <string>

namespace hytte {

// An Incident is registered in the history when it is created (Team Guide §9, deviation D20).
void IncidentHistory::registerIncident()
{
    std::string id = "I-" + std::to_string(incidents_.size() + 1);
    incidents_.push_back(std::unique_ptr<Incident>(new Incident(id, "")));
}

// Mock-up: the SAME record would be updated here (Team Guide §9).
void IncidentHistory::updateIncident() {}

void IncidentHistory::viewHistory() {}

}  // namespace hytte
