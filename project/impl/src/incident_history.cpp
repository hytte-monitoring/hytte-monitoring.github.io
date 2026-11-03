#include "hytte/incident_history.hpp"

#include <string>

namespace hytte {

// An Incident is registered in the history when it is created (Team Guide §9, D20),
// starts as a Warning or a Critical Incident (F11), and knows the contacts to escalate to (D09).
void IncidentHistory::registerIncident(Severity severity, const std::vector<std::weak_ptr<EmergencyContact>>& contacts)
{
    // Full: make room by dropping the oldest closed Incident, or else the oldest (F13).
    if (incidents_.size() >= maxIncidents_)
    {
        auto oldest = incidents_.begin();
        for (auto it = incidents_.begin(); it != incidents_.end(); ++it)
        {
            if ((*it)->state() == Incident::State::Closed)
            {
                oldest = it;
                break;
            }
        }
        incidents_.erase(oldest);
    }

    // Ids keep counting after old Incidents are dropped, so the dashboard never sees one twice.
    // A function-local counter, because the class diagram has no attribute for it (D21).
    static int nextId = 1;
    std::string id = "I-" + std::to_string(nextId++);
    std::unique_ptr<Incident> incident(new Incident(id, "", severity, contacts));
    incident->handle(severity == Severity::CRITICAL ? Incident::Event::criticalDetected
                                                    : Incident::Event::warningDetected);
    incidents_.push_back(std::move(incident));
}

// Mock-up: the SAME record would be updated here (Team Guide §9).
void IncidentHistory::updateIncident() {}

// A copy of every Incident still on the board, oldest first (F12).
std::vector<Incident> IncidentHistory::viewHistory() const
{
    std::vector<Incident> copies;
    for (const std::unique_ptr<Incident>& incident : incidents_)
    {
        copies.push_back(*incident);
    }
    return copies;
}

// The live Incident with this id, or nullptr if it is not on the board (any more, D25).
Incident* IncidentHistory::findIncident(const std::string& incidentId)
{
    for (const std::unique_ptr<Incident>& incident : incidents_)
    {
        if (incident->getId() == incidentId)
        {
            return incident.get();
        }
    }
    return nullptr;
}

}  // namespace hytte
