#include "io/serial_link.hpp"

#include <cstdio>
#include <vector>

#include "MicroBit.h"

extern MicroBit uBit;

namespace io {

SerialLink::SerialLink(const hytte::IncidentHistory& history) : history_(history) {}

void SerialLink::send(const char* line)
{
    // Fibers take turns; keep one line from interleaving with another.
    while (sending_)
    {
        uBit.sleep(1);
    }
    sending_ = true;
    uBit.serial.send(ManagedString(line), SYNC_SLEEP);
    sending_ = false;
}

void SerialLink::sendHello() { send("{\"type\":\"hello\",\"firmware\":\"hytte-monitoring 0.1\"}\n"); }

void SerialLink::sendEvent(const char* sensor, const hytte::Cabin& cabin)
{
    char line[96];
    snprintf(line, sizeof line, "{\"type\":\"event\",\"sensor\":\"%s\",\"mode\":\"%s\"}\n", sensor, modeName(cabin.state()));
    send(line);
}

void SerialLink::sendMode(const hytte::Cabin& cabin)
{
    char line[64];
    snprintf(line, sizeof line, "{\"type\":\"mode\",\"mode\":\"%s\"}\n", modeName(cabin.state()));
    send(line);
}

void SerialLink::sendLatency(const char* input, unsigned long microseconds)
{
    char line[80];
    snprintf(line, sizeof line, "{\"type\":\"latency\",\"input\":\"%s\",\"us\":%lu}\n", input, microseconds);
    send(line);
}

void SerialLink::sendNote(const char* message)
{
    char line[128];
    snprintf(line, sizeof line, "{\"type\":\"note\",\"message\":\"%s\"}\n", message);
    send(line);
}

void SerialLink::sendDisplay(const char* pattern)
{
    char line[64];
    snprintf(line, sizeof line, "{\"type\":\"display\",\"pattern\":\"%s\"}\n", pattern);
    send(line);
}

void SerialLink::sendIncidentChanges()
{
    std::map<std::string, hytte::Incident::State> now;
    for (const hytte::Incident& incident : history_.viewHistory())
    {
        now[incident.getId()] = incident.state();
        auto previous = sent_.find(incident.getId());
        if (previous != sent_.end() && previous->second == incident.state())
        {
            continue;
        }
        char line[128];
        snprintf(line, sizeof line, "{\"type\":\"incident\",\"id\":\"%s\",\"severity\":\"%s\",\"state\":\"%s\"}\n",
                 incident.getId().c_str(), severityName(incident.getSeverity()), stateName(incident.state()));
        send(line);
    }
    sent_ = now;   // Incidents dropped by the history limit (F13) are forgotten here too
}

const char* modeName(hytte::Cabin::State state)
{
    switch (state)
    {
        case hytte::Cabin::State::Home:
        case hytte::Cabin::State::HomeCold: return "HOME";
        case hytte::Cabin::State::Away:
        case hytte::Cabin::State::AwayCold: return "AWAY";
        default: return "NONE";
    }
}

const char* severityName(hytte::Severity severity)
{
    return severity == hytte::Severity::CRITICAL ? "CRITICAL" : "WARNING";
}

const char* stateName(hytte::Incident::State state)
{
    switch (state)
    {
        case hytte::Incident::State::New: return "New";
        case hytte::Incident::State::Warning: return "Warning";
        case hytte::Incident::State::Critical: return "Critical";
        case hytte::Incident::State::Closed: return "Closed";
    }
    return "?";
}

}  // namespace io
