#pragma once

namespace climate {

class Heater
{
public:
    void turnOn();
    void turnOff();
    bool isOn() const;

private:
    bool on_ = false;
};

}  // namespace climate
