// The scenario of diagrams/input/sequence-smoke_escalation.drawio.
//
// main() sets the objects up; scenario() makes the calls the diagram shows, and only those
// are recorded. The verifier runs this program in a traced build.
#include <memory>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/monitoring_system.hpp"

namespace {

void scenario(hytte::MonitoringSystem& system)
{
    system.evaluateEvent();   // SmokeSensor -> MonitoringSystem : evaluateEvent()
}

}  // namespace

int main()
{
    hytte::Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    auto contact = std::make_shared<hytte::EmergencyContact>("e1", "Family member", "+47 000 00 000");
    hytte::MonitoringSystem system(cabin, history, {contact});
    scenario(system);
    return 0;
}
