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

void SerialLink::sendHistory()
{
    std::vector<hytte::Incident> incidents = history_.viewHistory();
    char line[400];
    int n = snprintf(line, sizeof line, "{\"type\":\"history\",\"states\":[");
    for (std::size_t i = 0; i < incidents.size() && n < static_cast<int>(sizeof line) - 16; ++i)
    {
        n += snprintf(line + n, sizeof line - n, "%s\"%s\"", i == 0 ? "" : ",", stateName(incidents[i].state()));
    }
    snprintf(line + n, sizeof line - n, "]}\n");
    send(line);
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
