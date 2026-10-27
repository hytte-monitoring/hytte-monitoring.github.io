#pragma once

// Board -> dashboard: one JSON object per line on the USB serial port (spec §5).
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
    // Sends every Incident on the board, oldest first. The model gives an Incident no
    // readable id or severity yet (finding F16), so the state is all that is sent.
    void sendHistory();

private:
    void send(const char* line);

    const hytte::IncidentHistory& history_;
    bool sending_ = false;
};

const char* modeName(hytte::Cabin::State state);
const char* stateName(hytte::Incident::State state);

}  // namespace io
