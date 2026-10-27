#pragma once

#include <string>

namespace lending {

class Book
{
public:
    Book(std::string id, std::string title);

    std::string getId() const;
    std::string getTitle() const;
    bool isAvailable() const;
    void markOnLoan();
    void markReturned();

private:
    std::string id_;
    std::string title_;
    bool onLoan_ = false;
};

}  // namespace lending
