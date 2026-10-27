#include "library/loan_validator.hpp"

namespace library {

LoanValidator::LoanValidator(int graceDays) : graceDays_(graceDays) {}

bool LoanValidator::validate(const Loan& loan, Date today) const
{
    (void)graceDays_;
    return !loan.isOverdue(today);
}

}  // namespace library
