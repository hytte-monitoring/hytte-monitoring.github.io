#pragma once

#include <string>

namespace library {

class Date
{
public:
    Date() = default;
    Date(int year, int month, int day);

    std::string toIso() const;
    static Date today();

    // Operator overloads are omitted from diagrams by the mapping contract.
    bool operator<(const Date& other) const;

private:
    int year_ = 1970;
    int month_ = 1;
    int day_ = 1;
};

}  // namespace library
