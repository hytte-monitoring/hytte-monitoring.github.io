#pragma once

#include <memory>
#include <optional>

#include "library/date.hpp"
#include "library/library_item.hpp"
#include "library/member.hpp"

namespace library {

class Loan
{
public:
    Loan(std::shared_ptr<LibraryItem> item, std::shared_ptr<Member> borrower, Date dueDate);

    bool isOverdue(Date today) const;
    Date getDueDate() const;
    void close(Date on);

private:
    Date dueDate_;                          // by value      -> composition "1"
    std::optional<Date> returnedOn_;        // optional      -> composition "0..1"
    std::shared_ptr<LibraryItem> item_;     // shared_ptr    -> aggregation

    // DELIBERATE MISTAKE (changed): the design specifies `Member*`, an ASSOCIATION —
    // a loan refers to its borrower, it does not co-own them. Implemented here as a
    // shared_ptr, which the extractor reads as AGGREGATION. See README.md.
    std::shared_ptr<Member> borrower_;
};

}  // namespace library
