#include "lending/catalog.hpp"

#include <utility>

namespace lending {

void Catalog::add(Book book)
{
    const std::string id = book.getId();
    books_.insert_or_assign(id, std::move(book));
}

Book* Catalog::find(const std::string& id)
{
    const auto found = books_.find(id);
    return found == books_.end() ? nullptr : &found->second;
}

}  // namespace lending
