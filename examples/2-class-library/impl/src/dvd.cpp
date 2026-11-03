#include "library/dvd.hpp"

#include <utility>

namespace library {

Dvd::Dvd(std::string id, std::string title, int durationMinutes)
    : LibraryItem(std::move(id), std::move(title)), durationMinutes_(durationMinutes)
{
}

std::string Dvd::displayName() const { return title_ + " (dvd, " + std::to_string(durationMinutes_) + "min)"; }

bool Dvd::matches(const std::string& query) const
{
    return title_.find(query) != std::string::npos;
}

}  // namespace library
