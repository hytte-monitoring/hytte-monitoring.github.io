#pragma once

#include <string>
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
    std::vector<Cabin*> cabins_;
    std::vector<EmergencyContact*> contacts_;
    std::vector<Incident*> incidents_;
};

}  // namespace hytte
