#include "library/library_item.hpp"

#include <utility>

namespace library {

LibraryItem::LibraryItem(std::string id, std::string title)
    : id_(std::move(id)), title_(std::move(title))
{
}

std::string LibraryItem::getId() const { return id_; }

ItemStatus LibraryItem::getStatus() const { return status_; }

void LibraryItem::setStatus(ItemStatus s) { status_ = s; }

}  // namespace library
