#pragma once

#include <string>

namespace hytte {

/// Abstract: has a pure virtual method AND data members.
class Sensor
{
public:
    explicit Sensor(std::string sensorID);
    virtual ~Sensor() = default;

    void monitor();
    virtual void detectCondition() = 0;

private:
    std::string sensorID_;
    bool enabled_ = true;
};

}  // namespace hytte
