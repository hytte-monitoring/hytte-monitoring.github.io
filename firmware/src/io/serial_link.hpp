#pragma once

// Board -> dashboard: one JSON object per line on the USB serial port (spec §5).
#include <map>
#include <string>

#include "hytte/cabin.hpp"
#include "hytte/incident_history.hpp"

namespace io {

class SerialLink
{
public:
    explicit SerialLink(const hytte::IncidentHistory& history);

    void sendHello();
    void sendEvent(const char* sensor, const hytte::Cabin& cabin);
    void sendMode(const hytte::Cabin& cabin);
    void sendLatency(const char* input, unsigned long microseconds);
    void sendNote(const char* message);
    void sendDisplay(const char* pattern);
    // Sends one `incident` line for every Incident that is new or has changed since the
    // last call, with its id, severity and state (spec §5, F16).
    void sendIncidentChanges();

private:
    void send(const char* line);

    const hytte::IncidentHistory& history_;
    bool sending_ = false;
    std::map<std::string, hytte::Incident::State> sent_;   // id -> state last sent
};

const char* modeName(hytte::Cabin::State state);
const char* stateName(hytte::Incident::State state);
const char* severityName(hytte::Severity severity);

}  // namespace io
