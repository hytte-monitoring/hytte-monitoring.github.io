#pragma once

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

#include "library/catalog.hpp"
#include "library/loan.hpp"
#include "library/member.hpp"
#include "library/search_query.hpp"

namespace library {

class Library
{
public:
    explicit Library(std::string name);

    void addItem(std::unique_ptr<LibraryItem> item);
    std::vector<LibraryItem*> search(const SearchQuery& q) const;
    std::shared_ptr<Loan> lend(const std::string& itemId, const std::string& memberId);
    std::size_t itemCount() const;
    static int openCount();

    void enrol(Member m);

private:
    std::string name_;
    std::vector<std::unique_ptr<LibraryItem>> items_;   // composition "*"
    std::vector<std::shared_ptr<Loan>> loans_;          // aggregation "*"
    Catalog<Member> members_;                           // by value -> composition "1"
};

}  // namespace library
