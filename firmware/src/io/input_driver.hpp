#pragma once

// Board inputs -> model events (spec §3):
//   button A    DoorSensor: the door opened  -> Cabin doorOpened
//   shake       SmokeSensor: smoke detected  -> MonitoringSystem evaluateEvent()
//   buttons A+B the owner changes mode       -> Cabin ownerSelectsHome / ownerSelectsAway
//   button B    the owner resolves           -> not possible through the model yet (F15)
#include "hytte/cabin.hpp"
#include "hytte/monitoring_system.hpp"
#include "io/output_driver.hpp"
#include "io/serial_link.hpp"

namespace io {

class InputDriver
{
public:
    InputDriver(hytte::Cabin& cabin, hytte::MonitoringSystem& system, OutputDriver& output, SerialLink& serial);

    // Registers the button and gesture listeners on the micro:bit's message bus.
    void start();

    void onDoor();
    void onSmoke();
    void onModeChange();
    void onResolve();

private:
    hytte::Cabin& cabin_;
    hytte::MonitoringSystem& system_;
    OutputDriver& output_;
    SerialLink& serial_;
};

}  // namespace io
