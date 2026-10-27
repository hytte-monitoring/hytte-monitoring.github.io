// Unit tests for Cabin.changeMode() (Team Guide §6, deviation D07)
// and Sensor.monitor() (Team Guide §4, deviation D08).
#include "check.hpp"
#include "test_access.hpp"

#include "hytte/sensor.hpp"

using hytte::MonitoringMode;
using hytte::TestAccess;

namespace {

// A sensor that counts how often it is asked to detect its condition.
class CountingSensor : public hytte::Sensor
{
public:
    using Sensor::Sensor;
    void detectCondition() override { ++detections; }
    int detections = 0;
};

void cabinStartsHomeAndSwitchesMode()
{
    hytte::Cabin cabin("c1", "Hytte");
    CHECK(TestAccess::mode(cabin) == MonitoringMode::HOME);
    cabin.changeMode();
    CHECK(TestAccess::mode(cabin) == MonitoringMode::AWAY);
    cabin.changeMode();
    CHECK(TestAccess::mode(cabin) == MonitoringMode::HOME);
}

void enabledSensorDetectsOnMonitor()
{
    CountingSensor sensor("s1");
    sensor.monitor();
    sensor.monitor();
    CHECK(sensor.detections == 2);
}

}  // namespace

int main()
{
    cabinStartsHomeAndSwitchesMode();
    enabledSensorDetectsOnMonitor();
    return test::finish("test_cabin_and_sensor");
}
