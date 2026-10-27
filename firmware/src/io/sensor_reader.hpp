#pragma once

// Extra board sensors, for DISPLAY ONLY: every 2 s their values go to the dashboard as a
// `reading` line. They do not go through the model and never create Incidents.
//   temperature  the processor's thermometer (reads a little warm) -> indoor temperature
//   touch logo   touched = wet                                      -> water leak
//   microphone   sound level in dB                                 -> activity in the cabin
#include "io/serial_link.hpp"

namespace io {

class SensorReader
{
public:
    explicit SensorReader(SerialLink& serial);

    // Runs forever in its own fiber.
    void run();

private:
    SerialLink& serial_;
};

}  // namespace io
