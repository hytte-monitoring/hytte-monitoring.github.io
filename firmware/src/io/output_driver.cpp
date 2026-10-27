#include "io/output_driver.hpp"

#include <vector>

#include "MicroBit.h"

extern MicroBit uBit;

namespace io {

namespace {

// The newest Incident that is still active, or New if there is none.
hytte::Incident::State activeIncidentState(const hytte::IncidentHistory& history)
{
    std::vector<hytte::Incident> incidents = history.viewHistory();
    for (auto it = incidents.rbegin(); it != incidents.rend(); ++it)
    {
        hytte::Incident::State state = it->state();
        if (state == hytte::Incident::State::Warning || state == hytte::Incident::State::Critical)
        {
            return state;
        }
    }
    return hytte::Incident::State::New;
}

char modeLetter(hytte::Cabin::State state)
{
    switch (state)
    {
        case hytte::Cabin::State::Home:
        case hytte::Cabin::State::HomeCold: return 'H';
        case hytte::Cabin::State::Away:
        case hytte::Cabin::State::AwayCold: return 'A';
        default: return '?';   // Awaiting: the owner has not chosen a mode yet
    }
}

void fill(int brightness)
{
    for (int x = 0; x < 5; ++x)
    {
        for (int y = 0; y < 5; ++y)
        {
            uBit.display.image.setPixelValue(x, y, brightness);
        }
    }
}

}  // namespace

OutputDriver::OutputDriver(const hytte::Cabin& cabin, const hytte::IncidentHistory& history)
    : cabin_(cabin), history_(history)
{
}

void OutputDriver::showResolved()
{
    static const MicroBitImage tick("0,0,0,0,0\n0,0,0,0,255\n0,0,0,255,0\n255,0,255,0,0\n0,255,0,0,0\n");
    uBit.display.print(tick);
    tickUntil_ = uBit.systemTime() + 800;
}

void OutputDriver::show(bool blinkOn)
{
    if (uBit.systemTime() < tickUntil_)
    {
        return;   // keep the tick on screen a little longer
    }
    switch (activeIncidentState(history_))
    {
        case hytte::Incident::State::Critical:
            fill(blinkOn ? 255 : 0);   // flashing full matrix
            break;
        case hytte::Incident::State::Warning:
            if (blinkOn)
            {
                uBit.display.printChar('!');   // blinking "!"
            }
            else
            {
                uBit.display.clear();
            }
            break;
        default:
            uBit.display.printChar(modeLetter(cabin_.state()));
            break;
    }
}

void OutputDriver::run()
{
    bool blinkOn = true;
    while (true)
    {
        show(blinkOn);
        blinkOn = !blinkOn;
        uBit.sleep(250);
    }
}

}  // namespace io
