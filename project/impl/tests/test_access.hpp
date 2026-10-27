#pragma once

// Read access to private model state, for the unit tests only.
// The class diagram has no getters, so the tests use the friend declaration
// `friend struct TestAccess;` in Incident, Cabin, MonitoringSystem and IncidentHistory instead of adding
// methods. Incident and Cabin have state() getters, and Incident has getId() and
// getSeverity() in the model (team decisions F01, F04, F16).
#include <string>

#include "hytte/cabin.hpp"
#include "hytte/incident.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/monitoring_system.hpp"

namespace hytte {

struct TestAccess
{
    static IncidentStatus status(const Incident& incident) { return incident.status_; }
    static bool contactsConfigured(const Incident& incident) { return incident.contactsConfigured(); }
    static MonitoringMode mode(const Cabin& cabin) { return cabin.mode_; }
    static bool coldProtectionActive(const Cabin& cabin) { return cabin.coldProtectionActive_; }
    static MonitoringSystem::State state(const MonitoringSystem& system) { return system.state_; }
    static bool onBatteryBackup(const MonitoringSystem& system) { return system.onBatteryBackup_; }
    static bool cellularFallback(const MonitoringSystem& system) { return system.cellularFallback_; }
    static std::size_t incidentCount(const IncidentHistory& history) { return history.incidents_.size(); }
};

}  // namespace hytte
