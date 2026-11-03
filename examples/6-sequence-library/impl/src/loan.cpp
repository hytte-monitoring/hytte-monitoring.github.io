#include "lending/loan.hpp"

namespace lending {

Loan::Loan(int id, Book* book, Member* member) : id_(id), book_(book), member_(member) {}

int Loan::getId() const { return id_; }

Book* Loan::getBook() const { return book_; }

Member* Loan::getMember() const { return member_; }

}  // namespace lending
