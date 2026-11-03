#pragma once

#include <string>

namespace library {

/// Interface-shaped: every method pure virtual, no data members, virtual destructor.
class Searchable
{
public:
    virtual ~Searchable() = default;

    virtual bool matches(const std::string& query) const = 0;
};

}  // namespace library
