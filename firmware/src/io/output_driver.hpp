#pragma once

// Model state -> the 5x5 LED matrix (spec §3).
#include "hytte/cabin.hpp"
#include "hytte/incident_history.hpp"

namespace io {

class OutputDriver
{
public:
    OutputDriver(const hytte::Cabin& cabin, const hytte::IncidentHistory& history);

    // Draws the current state. `blinkOn` is the phase of the blink for active Incidents.
    void show(bool blinkOn);
    // Shows a tick for a moment after the owner resolved an Incident (spec §3).
    void showResolved();
    // Runs forever in its own fiber: redraws every 250 ms so Incidents blink.
    void run();

private:
    const hytte::Cabin& cabin_;
    const hytte::IncidentHistory& history_;
    unsigned long tickUntil_ = 0;   // system time in ms until which the tick stays
};

}  // namespace io
