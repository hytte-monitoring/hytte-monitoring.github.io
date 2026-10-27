#include <iostream>

#include "hytte/cabin.hpp"
#include "hytte/incident.hpp"
#include "hytte/monitoring_system.hpp"

int main()
{
    using Event = hytte::Incident::Event;
    hytte::Cabin cabin("c1", "Hytte");
    hytte::MonitoringSystem system(cabin);
    system.evaluateEvent();

    hytte::Incident incident("I-1", "2026-10-27T12:00");
    for (Event event : {Event::warningDetected, Event::conditionWorsens, Event::ownerResolved})
    {
        incident.handle(event);
    }
    std::cout << "demo done\n";
    return 0;
}
