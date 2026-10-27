// Unit tests for the System Operation page: state-cabin (monitoring mode and cold-weather
// protection, Team Guide §4 and §6) and state-monitoring_system (ADR-002).
#include "check.hpp"
#include "test_access.hpp"

#include <memory>
#include <string>
#include <vector>

#include "hytte/hytte_owner.hpp"

using hytte::Cabin;
using hytte::MonitoringMode;
using hytte::MonitoringSystem;
using hytte::TestAccess;

namespace {

void cabinWaitsForTheOwnerToChooseAMode()
{
    Cabin cabin("c1", "Hytte");
    CHECK(cabin.state() == Cabin::State::Awaiting);
}

void ownerChoosesAwayThenHome()
{
    Cabin cabin("c1", "Hytte");
    cabin.handle(Cabin::Event::ownerSelectsAway);
    CHECK(cabin.state() == Cabin::State::Away);
    CHECK(TestAccess::mode(cabin) == MonitoringMode::AWAY);
    cabin.handle(Cabin::Event::ownerSelectsHome);
    CHECK(cabin.state() == Cabin::State::Home);
    CHECK(TestAccess::mode(cabin) == MonitoringMode::HOME);
}

// Team Guide §4: cold weather makes protection active, and the mode is kept.
void coldWeatherActivatesAndDeactivatesProtection()
{
    Cabin cabin("c1", "Hytte");
    cabin.handle(Cabin::Event::ownerSelectsAway);
    cabin.handle(Cabin::Event::coldRequired);
    CHECK(cabin.state() == Cabin::State::AwayCold);
    CHECK(TestAccess::coldProtectionActive(cabin));
    CHECK(TestAccess::mode(cabin) == MonitoringMode::AWAY);
    cabin.handle(Cabin::Event::coldGone);
    CHECK(cabin.state() == Cabin::State::Away);
    CHECK(!TestAccess::coldProtectionActive(cabin));
}

// Team Guide §6: mode changes still work while cold-weather protection is active.
void modeChangesDuringColdProtection()
{
    Cabin cabin("c1", "Hytte");
    cabin.handle(Cabin::Event::coldRequired);
    cabin.handle(Cabin::Event::ownerSelectsHome);
    CHECK(cabin.state() == Cabin::State::HomeCold);
    cabin.handle(Cabin::Event::ownerSelectsAway);
    CHECK(cabin.state() == Cabin::State::AwayCold);
    CHECK(TestAccess::mode(cabin) == MonitoringMode::AWAY);
}

// Team Guide §6: in HOME, door and motion are normal and are ignored;
// in AWAY, they are handled (a security Warning is reported, finding F03).
void doorAndMotionAreOnlyHandledInAway()
{
    Cabin home("c1", "Hytte");
    home.handle(Cabin::Event::ownerSelectsHome);
    home.handle(Cabin::Event::doorOpened);
    home.handle(Cabin::Event::motionDetected);
    CHECK(home.state() == Cabin::State::Home);

    Cabin away("c2", "Hytte");
    away.handle(Cabin::Event::ownerSelectsAway);
    away.handle(Cabin::Event::doorOpened);
    away.handle(Cabin::Event::motionDetected);
    CHECK(away.state() == Cabin::State::Away);
}

// Team Guide §6 and §9: a door or motion event in AWAY creates and registers an Incident
// in the history (F03, F10); in HOME it does not.
void doorInAwayRegistersAnIncident()
{
    Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    MonitoringSystem system(cabin, history, {});

    cabin.handle(Cabin::Event::ownerSelectsHome);
    cabin.handle(Cabin::Event::doorOpened);
    CHECK(TestAccess::incidentCount(history) == 0);

    cabin.handle(Cabin::Event::ownerSelectsAway);
    cabin.handle(Cabin::Event::doorOpened);
    CHECK(TestAccess::incidentCount(history) == 1);
    // F11: a door Incident is a Warning.
    std::vector<hytte::Incident> incidents = history.viewHistory();
    CHECK(incidents.size() == 1 && incidents[0].state() == hytte::Incident::State::Warning);
    cabin.handle(Cabin::Event::motionDetected);
    CHECK(TestAccess::incidentCount(history) == 2);
}

// The smoke_escalation scenario registers one Incident.
void smokeRegistersAnIncident()
{
    Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    MonitoringSystem system(cabin, history, {});
    system.evaluateEvent();
    CHECK(TestAccess::incidentCount(history) == 1);
    // F11: a smoke Incident is Critical.
    std::vector<hytte::Incident> incidents = history.viewHistory();
    CHECK(incidents.size() == 1 && incidents[0].state() == hytte::Incident::State::Critical);
}

// F13: the board keeps at most 20 Incidents; when full, the oldest closed one goes first,
// and ids are never reused.
void historyKeepsTheLatestIncidents()
{
    hytte::IncidentHistory history;
    for (int i = 0; i < 25; ++i)
    {
        history.registerIncident(hytte::Severity::WARNING);
    }
    std::vector<hytte::Incident> incidents = history.viewHistory();
    CHECK(incidents.size() == 20);
    CHECK(incidents.front().getId() != incidents.back().getId());
    std::string firstKept = incidents.front().getId();
    history.registerIncident(hytte::Severity::CRITICAL);
    CHECK(TestAccess::incidentCount(history) == 20);
    CHECK(history.viewHistory().front().getId() != firstKept);
    CHECK(history.viewHistory().back().state() == hytte::Incident::State::Critical);
}

// Team Guide §8 (F15): the owner resolves an Incident by its id; it is closed, and the
// other Incidents are left alone. An unknown id does nothing.
void ownerResolvesAnIncidentById()
{
    hytte::IncidentHistory history;
    hytte::HytteOwner owner("u1", "Owner", history);
    history.registerIncident(hytte::Severity::WARNING);
    history.registerIncident(hytte::Severity::CRITICAL);
    std::vector<hytte::Incident> before = history.viewHistory();

    owner.resolveIncident(before[1].getId());
    std::vector<hytte::Incident> after = history.viewHistory();
    CHECK(after[1].state() == hytte::Incident::State::Closed);
    CHECK(after[0].state() == hytte::Incident::State::Warning);

    owner.resolveIncident("no-such-id");
    CHECK(history.viewHistory()[0].state() == hytte::Incident::State::Warning);
    CHECK(history.findIncident("no-such-id") == nullptr);
}

// ADR-002: battery backup on power failure, Cellular/SIM on Internet failure,
// both at once, and back to normal when they return.
void resilientMonitoringSwitchesAndRestores()
{
    Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    MonitoringSystem system(cabin, history, {});
    CHECK(TestAccess::state(system) == MonitoringSystem::State::ElectricityAndInternet);

    system.handle(MonitoringSystem::Event::powerLost);
    CHECK(TestAccess::onBatteryBackup(system));
    CHECK(!TestAccess::cellularFallback(system));

    system.handle(MonitoringSystem::Event::internetLost);
    CHECK(TestAccess::state(system) == MonitoringSystem::State::BatteryAndCellular);
    CHECK(TestAccess::onBatteryBackup(system));
    CHECK(TestAccess::cellularFallback(system));

    system.handle(MonitoringSystem::Event::powerRestored);
    system.handle(MonitoringSystem::Event::internetRestored);
    CHECK(TestAccess::state(system) == MonitoringSystem::State::ElectricityAndInternet);
    CHECK(!TestAccess::onBatteryBackup(system));
    CHECK(!TestAccess::cellularFallback(system));
}

}  // namespace

int main()
{
    cabinWaitsForTheOwnerToChooseAMode();
    ownerChoosesAwayThenHome();
    coldWeatherActivatesAndDeactivatesProtection();
    modeChangesDuringColdProtection();
    doorAndMotionAreOnlyHandledInAway();
    doorInAwayRegistersAnIncident();
    smokeRegistersAnIncident();
    historyKeepsTheLatestIncidents();
    ownerResolvesAnIncidentById();
    resilientMonitoringSwitchesAndRestores();
    return test::finish("test_system_operation");
}
