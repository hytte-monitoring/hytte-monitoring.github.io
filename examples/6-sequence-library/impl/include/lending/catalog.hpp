#pragma once

#include <map>
#include <string>

#include "lending/book.hpp"

namespace lending {

class Catalog
{
public:
    void add(Book book);
    Book* find(const std::string& id);

private:
    std::map<std::string, Book> books_;   // by value, many -> composition "*"
};

}  // namespace lending
