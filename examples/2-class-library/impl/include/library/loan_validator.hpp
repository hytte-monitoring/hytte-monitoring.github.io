#pragma once

#include "library/date.hpp"
#include "library/loan.hpp"

namespace library {

// DELIBERATE MISTAKE (extra): this class does not appear in the design at all.
// It is the kind of helper an AI commonly invents unprompted. See README.md.
class LoanValidator
{
public:
    explicit LoanValidator(int graceDays);

    bool validate(const Loan& loan, Date today) const;

private:
    int graceDays_ = 0;
};

}  // namespace library
