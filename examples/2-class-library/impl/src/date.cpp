#include "library/date.hpp"

#include <cstdio>
#include <ctime>

namespace library {

Date::Date(int year, int month, int day) : year_(year), month_(month), day_(day) {}

std::string Date::toIso() const
{
    char buffer[11];
    std::snprintf(buffer, sizeof(buffer), "%04d-%02d-%02d", year_, month_, day_);
    return std::string(buffer);
}

Date Date::today()
{
    const std::time_t now = std::time(nullptr);
    const std::tm* local = std::localtime(&now);
    return Date(local->tm_year + 1900, local->tm_mon + 1, local->tm_mday);
}

bool Date::operator<(const Date& other) const
{
    if (year_ != other.year_) return year_ < other.year_;
    if (month_ != other.month_) return month_ < other.month_;
    return day_ < other.day_;
}

}  // namespace library
