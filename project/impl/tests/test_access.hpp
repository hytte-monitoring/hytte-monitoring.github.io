#pragma once

// Read access to private model state, for the unit tests only.
// The class diagram has no getters, so the tests use the friend declaration
// `friend struct TestAccess;` in Incident and Cabin instead of adding methods.
#include <string>

#include "hytte/cabin.hpp"
#include "hytte/incident.hpp"

namespace hytte {

struct TestAccess
{
    static Incident::State state(const Incident& incident) { return incident.state_; }
    static Severity severity(const Incident& incident) { return incident.severity_; }
    static IncidentStatus status(const Incident& incident) { return incident.status_; }
    static std::string id(const Incident& incident) { return incident.incidentId_; }
    static MonitoringMode mode(const Cabin& cabin) { return cabin.mode_; }
};

}  // namespace hytte
