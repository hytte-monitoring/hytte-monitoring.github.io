#pragma once

#include <string>
#include <memory>
#include <vector>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident.hpp"
#include "hytte/incident_history.hpp"

namespace hytte {

class HytteOwner
{
public:
    HytteOwner(std::string userID, std::string name, IncidentHistory& history);

    void configureMonitoring();
    void changeMode();
    void resolveIncident(const std::string& incidentId);

private:
    std::string userID_;
    std::string name_;
    std::vector<std::weak_ptr<Cabin>> cabins_;
    std::vector<std::weak_ptr<EmergencyContact>> contacts_;
    std::vector<std::weak_ptr<Incident>> incidents_;
    IncidentHistory* history_;
};

}  // namespace hytte
