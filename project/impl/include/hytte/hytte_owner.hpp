#pragma once

#include <string>
#include <memory>
#include <vector>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident.hpp"

namespace hytte {

class HytteOwner
{
public:
    HytteOwner(std::string userID, std::string name);

    void configureMonitoring();
    void changeMode();
    void resolveIncident();

private:
    std::string userID_;
    std::string name_;
    std::vector<std::weak_ptr<Cabin>> cabins_;
    std::vector<std::weak_ptr<EmergencyContact>> contacts_;
    std::vector<std::weak_ptr<Incident>> incidents_;
};

}  // namespace hytte
