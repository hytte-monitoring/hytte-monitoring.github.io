#pragma once

#include <map>
#include <string>
#include <vector>

#include "lending/catalog.hpp"
#include "lending/loan.hpp"
#include "lending/member.hpp"

namespace lending {

class Library
{
public:
    void addBook(const std::string& id, const std::string& title);
    void enrol(const std::string& id, const std::string& name);
    bool lend(const std::string& bookId, const std::string& memberId);
    void giveBack(const std::string& bookId);

private:
    Member* findMember(const std::string& id);
    int nextLoanId() const;

    Catalog catalog_;                        // by value -> composition
    std::map<std::string, Member> members_;  // composition "*"
    std::vector<Loan> loans_;                // composition "*"
};

}  // namespace lending
