#include "library/book.hpp"

#include <algorithm>
#include <utility>

namespace library {

Book::Book(std::string id, std::string title, std::string isbn, int pageCount)
    : LibraryItem(std::move(id), std::move(title)), isbn_(std::move(isbn)), pageCount_(pageCount)
{
}

std::string Book::displayName() const { return title_ + " (book, " + std::to_string(pageCount_) + "pp)"; }

bool Book::matches(const std::string& query) const
{
    return title_.find(query) != std::string::npos || isbn_.find(query) != std::string::npos;
}

std::string Book::getIsbn() const { return isbn_; }

}  // namespace library
