#include "io/input_driver.hpp"

#include "MicroBit.h"

extern MicroBit uBit;

namespace io {

namespace {

InputDriver* driver = nullptr;   // the message bus calls plain functions

void onButtonA(MicroBitEvent) { driver->onDoor(); }
void onButtonB(MicroBitEvent) { driver->onResolve(); }
void onButtonAB(MicroBitEvent) { driver->onModeChange(); }
void onShake(MicroBitEvent) { driver->onSmoke(); }

}  // namespace

InputDriver::InputDriver(hytte::Cabin& cabin, hytte::MonitoringSystem& system, OutputDriver& output, SerialLink& serial)
    : cabin_(cabin), system_(system), output_(output), serial_(serial)
{
}

void InputDriver::start()
{
    driver = this;
    uBit.messageBus.listen(MICROBIT_ID_BUTTON_A, MICROBIT_BUTTON_EVT_CLICK, onButtonA);
    uBit.messageBus.listen(MICROBIT_ID_BUTTON_B, MICROBIT_BUTTON_EVT_CLICK, onButtonB);
    uBit.messageBus.listen(MICROBIT_ID_BUTTON_AB, MICROBIT_BUTTON_EVT_CLICK, onButtonAB);
    uBit.messageBus.listen(MICROBIT_ID_GESTURE, MICROBIT_ACCELEROMETER_EVT_SHAKE, onShake);
}

// The model decides: in AWAY the Cabin creates a Warning Incident, in HOME nothing happens.
void InputDriver::onDoor()
{
    unsigned long start = system_timer_current_time_us();
    cabin_.handle(hytte::Cabin::Event::doorOpened);
    output_.show(true);
    unsigned long elapsed = system_timer_current_time_us() - start;
    serial_.sendEvent("door", cabin_);
    serial_.sendHistory();
    serial_.sendLatency("door", elapsed);
}

void InputDriver::onSmoke()
{
    unsigned long start = system_timer_current_time_us();
    system_.evaluateEvent();
    output_.show(true);
    unsigned long elapsed = system_timer_current_time_us() - start;
    serial_.sendEvent("smoke", cabin_);
    serial_.sendHistory();
    serial_.sendLatency("smoke", elapsed);
}

// One button pair for both choices: from HOME go AWAY, otherwise go HOME.
void InputDriver::onModeChange()
{
    hytte::Cabin::State state = cabin_.state();
    bool home = state == hytte::Cabin::State::Home || state == hytte::Cabin::State::HomeCold;
    cabin_.handle(home ? hytte::Cabin::Event::ownerSelectsAway : hytte::Cabin::Event::ownerSelectsHome);
    output_.show(true);
    serial_.sendMode(cabin_);
}

void InputDriver::onResolve() { serial_.sendNote("resolve is not possible through the model yet (finding F15)"); }

}  // namespace io
