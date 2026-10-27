#include <iostream>
#include <memory>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/incident.hpp"
#include "hytte/monitoring_system.hpp"

int main()
{
    using Event = hytte::Incident::Event;
    hytte::Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    auto contact = std::make_shared<hytte::EmergencyContact>("e1", "Family member", "+47 000 00 000");
    hytte::MonitoringSystem system(cabin, history, {contact});
    system.evaluateEvent();

    hytte::Incident incident("I-1", "2026-10-27T12:00");
    for (Event event : {Event::warningDetected, Event::conditionWorsens, Event::ownerResolved})
    {
        incident.handle(event);
    }
    std::cout << "demo done\n";
    return 0;
}
