#include "io/output_driver.hpp"

#include <cstring>
#include <vector>

#include "MicroBit.h"

extern MicroBit uBit;

namespace io {

namespace {

// The most serious active Incident: Critical before Warning, so a Critical Incident is
// never hidden behind a newer Warning (ADR-001). New if no Incident is active.
hytte::Incident::State mostSeriousActiveState(const hytte::IncidentHistory& history)
{
    hytte::Incident::State result = hytte::Incident::State::New;
    for (const hytte::Incident& incident : history.viewHistory())
    {
        if (incident.state() == hytte::Incident::State::Critical)
        {
            return hytte::Incident::State::Critical;
        }
        if (incident.state() == hytte::Incident::State::Warning)
        {
            result = hytte::Incident::State::Warning;
        }
    }
    return result;
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

OutputDriver::OutputDriver(const hytte::Cabin& cabin, const hytte::IncidentHistory& history, SerialLink& serial)
    : cabin_(cabin), history_(history), serial_(serial)
{
}

void OutputDriver::showResolved()
{
    static const MicroBitImage tick("0,0,0,0,0\n0,0,0,0,255\n0,0,0,255,0\n255,0,255,0,0\n0,255,0,0,0\n");
    uBit.display.print(tick);
    tickUntil_ = uBit.systemTime() + 800;
    pattern_ = "tick";
}

void OutputDriver::show(bool blinkOn)
{
    if (uBit.systemTime() < tickUntil_)
    {
        return;   // keep the tick on screen a little longer
    }
    const char* pattern = "?";
    switch (mostSeriousActiveState(history_))
    {
        case hytte::Incident::State::Critical:
            fill(blinkOn ? 255 : 0);   // flashing full matrix
            pattern = "critical";
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
            pattern = "warning";
            break;
        default:
        {
            char letter = modeLetter(cabin_.state());
            uBit.display.printChar(letter);
            pattern = letter == 'H' ? "H" : (letter == 'A' ? "A" : "?");
            break;
        }
    }
    pattern_ = pattern;
}

void OutputDriver::run()
{
    bool blinkOn = true;
    while (true)
    {
        show(blinkOn);
        if (std::strcmp(pattern_, reported_) != 0)
        {
            reported_ = pattern_;
            serial_.sendDisplay(pattern_);
        }
        blinkOn = !blinkOn;
        uBit.sleep(250);
    }
}

}  // namespace io
