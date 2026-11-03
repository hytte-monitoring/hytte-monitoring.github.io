#include "library/search_query.hpp"

#include <utility>

namespace library {

SearchQuery::SearchQuery(std::string text, bool includeOnLoan)
    : text_(std::move(text)), includeOnLoan_(includeOnLoan)
{
}

std::string SearchQuery::text() const { return text_; }

bool SearchQuery::includeOnLoan() const { return includeOnLoan_; }

}  // namespace library
