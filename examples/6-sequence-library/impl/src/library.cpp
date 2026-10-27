#include "lending/library.hpp"

#include <algorithm>
#include <iostream>

namespace lending {

void Library::addBook(const std::string& id, const std::string& title)
{
    catalog_.add(Book(id, title));
}

void Library::enrol(const std::string& id, const std::string& name)
{
    members_.insert_or_assign(id, Member(id, name));
}

bool Library::lend(const std::string& bookId, const std::string& memberId)
{
    Book* book = catalog_.find(bookId);
    if (book == nullptr || !book->isAvailable())
    {
        return false;
    }
    // MISTAKE 1 (extra): the design draws no call to getTitle().
    std::cout << "lending " << book->getTitle() << "\n";
    // MISTAKE 2 (changed): the design marks the book on loan *after* finding the member.
    book->markOnLoan();
    Member* member = findMember(memberId);
    if (member == nullptr)
    {
        book->markReturned();
        return false;
    }
    // nextLoanId() is a call to itself the design does not draw: not counted.
    loans_.emplace_back(nextLoanId(), book, member);
    return true;
}

void Library::giveBack(const std::string& bookId)
{
    Book* book = catalog_.find(bookId);
    if (book == nullptr)
    {
        return;
    }
    // MISTAKE 3 (missing): the design's Library -> Book : markReturned() is not here, so the
    // book stays on loan for ever.
    std::erase_if(loans_, [book](const Loan& loan) { return loan.getBook() == book; });
}

Member* Library::findMember(const std::string& id)
{
    const auto found = members_.find(id);
    return found == members_.end() ? nullptr : &found->second;
}

int Library::nextLoanId() const { return static_cast<int>(loans_.size()) + 1; }

}  // namespace lending
