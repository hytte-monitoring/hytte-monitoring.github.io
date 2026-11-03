#include "io/sensor_reader.hpp"

#include "MicroBit.h"

extern MicroBit uBit;

namespace io {

SensorReader::SensorReader(SerialLink& serial) : serial_(serial) {}

void SensorReader::run()
{
    while (true)
    {
        int temperature = uBit.thermometer.getTemperature();
        bool wet = uBit.logo.isPressed();
        int sound = static_cast<int>(uBit.audio.levelSPL->getValue(LEVEL_DETECTOR_SPL_DB));
        serial_.sendReading(temperature, wet, sound);
        uBit.sleep(2000);
    }
}

}  // namespace io
