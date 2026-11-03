#pragma once

#include <string>

#include "library/library_item.hpp"
#include "library/searchable.hpp"

namespace library {

class Book : public LibraryItem, public Searchable
{
public:
    Book(std::string id, std::string title, std::string isbn, int pageCount);

    std::string displayName() const override;
    bool matches(const std::string& query) const override;
    std::string getIsbn() const;

private:
    std::string isbn_;
    int pageCount_ = 0;
};

}  // namespace library
