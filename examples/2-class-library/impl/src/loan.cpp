#include "library/loan.hpp"

#include <utility>

namespace library {

Loan::Loan(std::shared_ptr<LibraryItem> item, std::shared_ptr<Member> borrower, Date dueDate)
    : dueDate_(dueDate), item_(std::move(item)), borrower_(std::move(borrower))
{
}

bool Loan::isOverdue(Date today) const
{
    if (returnedOn_.has_value()) return false;
    return dueDate_ < today;
}

Date Loan::getDueDate() const { return dueDate_; }

void Loan::close(Date on) { returnedOn_ = on; }

}  // namespace library
