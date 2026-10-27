#pragma once

#include <string>

namespace library {

class SearchQuery
{
public:
    SearchQuery(std::string text, bool includeOnLoan);

    std::string text() const;
    bool includeOnLoan() const;

private:
    std::string text_;
    bool includeOnLoan_ = false;
};

}  // namespace library
