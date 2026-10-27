#include "lending/book.hpp"

#include <utility>

namespace lending {

Book::Book(std::string id, std::string title) : id_(std::move(id)), title_(std::move(title)) {}

std::string Book::getId() const { return id_; }

std::string Book::getTitle() const { return title_; }

bool Book::isAvailable() const { return !onLoan_; }

void Book::markOnLoan() { onLoan_ = true; }

void Book::markReturned() { onLoan_ = false; }

}  // namespace lending
