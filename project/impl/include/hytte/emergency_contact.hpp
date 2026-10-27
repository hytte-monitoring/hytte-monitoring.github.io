#pragma once

#include <string>

namespace hytte {

class EmergencyContact
{
public:
    EmergencyContact(std::string contactID, std::string name, std::string contactInfo);

    void receiveNotification();

private:
    std::string contactID_;
    std::string name_;
    std::string contactInfo_;
};

}  // namespace hytte
