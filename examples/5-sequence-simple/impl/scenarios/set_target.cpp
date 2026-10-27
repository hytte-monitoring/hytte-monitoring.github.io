// The scenario of diagrams/input/sequence-set_target.drawio.
//
// main() sets the objects up; scenario() makes the calls the diagram shows, and only those
// are recorded. The verifier runs this program in a traced build.
#include "climate/thermostat.hpp"

namespace {

void scenario(climate::Thermostat& thermostat)
{
    thermostat.setTarget(21.0);   // User -> Thermostat : setTarget(21)
}

}  // namespace

int main()
{
    climate::Sensor sensor(18.5);
    climate::Heater heater;
    climate::Thermostat thermostat(sensor, heater);
    scenario(thermostat);
    return 0;
}
