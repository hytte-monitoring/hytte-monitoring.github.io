#include "hytte/emergency_contact.hpp"

#include <utility>

namespace hytte {

EmergencyContact::EmergencyContact(std::string contactID, std::string name, std::string contactInfo)
    : contactID_(std::move(contactID)), name_(std::move(name)), contactInfo_(std::move(contactInfo))
{
}

// Mock-up: no real SMS or call (Team Guide §17).
void EmergencyContact::receiveNotification() {}

}  // namespace hytte
