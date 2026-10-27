#pragma once

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

namespace library {

/// Generic container. `T` is a template parameter, not a project type, so `entries`
/// stays an attribute rather than becoming a relation.
template <typename T>
class Catalog
{
public:
    void add(T item) { entries_.push_back(std::move(item)); }

    std::size_t size() const { return entries_.size(); }

    T* findById(const std::string& id)
    {
        for (auto& entry : entries_)
        {
            if (entry.getMemberId() == id)
            {
                return &entry;
            }
        }
        return nullptr;
    }

private:
    std::vector<T> entries_;
};

}  // namespace library
