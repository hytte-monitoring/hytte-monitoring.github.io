#pragma once

#include <string>

#include "library/library_item.hpp"
#include "library/searchable.hpp"

namespace library {

// DELIBERATE MISTAKE (missing): the design specifies `-int regionCode`.
// This implementation omits it. See README.md.
class Dvd : public LibraryItem, public Searchable
{
public:
    Dvd(std::string id, std::string title, int durationMinutes);

    std::string displayName() const override;
    bool matches(const std::string& query) const override;

private:
    int durationMinutes_ = 0;
};

}  // namespace library
