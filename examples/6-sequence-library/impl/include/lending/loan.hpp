#pragma once

#include "lending/book.hpp"
#include "lending/member.hpp"

namespace lending {

class Loan
{
public:
    Loan(int id, Book* book, Member* member);

    int getId() const;
    Book* getBook() const;
    Member* getMember() const;

private:
    int id_;
    Book* book_;       // raw pointers -> associations: a loan refers to its book and member
    Member* member_;
};

}  // namespace lending
