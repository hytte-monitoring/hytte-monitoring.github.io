#pragma once

namespace climate {

class Sensor
{
public:
    explicit Sensor(double reading);

    double read() const;

private:
    double reading_;
};

}  // namespace climate
