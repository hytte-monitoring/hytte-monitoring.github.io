// Hytte Monitoring on a micro:bit v2: the model from project/impl, unchanged, wired to the
// board's buttons, accelerometer, LED matrix and USB serial port. Wiring only, no logic.
#include <memory>

#include "MicroBit.h"
#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/hytte_owner.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/monitoring_system.hpp"
#include "io/input_driver.hpp"
#include "io/output_driver.hpp"
#include "io/sensor_reader.hpp"
#include "io/serial_link.hpp"

MicroBit uBit;

namespace {

hytte::Cabin* cabin;
hytte::IncidentHistory* history;
hytte::MonitoringSystem* monitoringSystem;
hytte::HytteOwner* owner;
io::OutputDriver* output;
io::SerialLink* serial;
io::InputDriver* input;
io::SensorReader* sensors;

void displayLoop() { output->run(); }
void sensorLoop() { sensors->run(); }

}  // namespace

int main()
{
    uBit.init();
    uBit.serial.setTxBufferSize(254);

    cabin = new hytte::Cabin("c1", "Hytte");
    history = new hytte::IncidentHistory();
    auto contact = std::make_shared<hytte::EmergencyContact>("e1", "Family member", "+47 000 00 000");
    monitoringSystem = new hytte::MonitoringSystem(*cabin, *history, {contact});
    owner = new hytte::HytteOwner("u1", "Owner", *history);

    serial = new io::SerialLink(*history);
    output = new io::OutputDriver(*cabin, *history, *serial);
    sensors = new io::SensorReader(*serial);
    input = new io::InputDriver(*cabin, *monitoringSystem, *owner, *history, *output, *serial);

    serial->sendHello();
    serial->sendMode(*cabin);
    input->start();

    create_fiber(displayLoop);
    create_fiber(sensorLoop);
    release_fiber();
}
