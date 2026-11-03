#pragma once

#include <string>

#include "library/item_status.hpp"

namespace library {

/// Abstract: has a pure virtual method AND data members.
class LibraryItem
{
public:
    LibraryItem(std::string id, std::string title);
    virtual ~LibraryItem() = default;

    virtual std::string displayName() const = 0;

    std::string getId() const;
    ItemStatus getStatus() const;
    void setStatus(ItemStatus s);

protected:
    std::string id_;
    std::string title_;
    ItemStatus status_ = ItemStatus::Available;
};

}  // namespace library
