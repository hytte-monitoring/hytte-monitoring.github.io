#include "library/library.hpp"

#include "library/searchable.hpp"

#include <utility>

namespace library {

namespace {
int g_openCount = 0;
}

Library::Library(std::string name) : name_(std::move(name)) { ++g_openCount; }

void Library::addItem(std::unique_ptr<LibraryItem> item) { items_.push_back(std::move(item)); }

void Library::enrol(Member m) { members_.add(std::move(m)); }

std::vector<LibraryItem*> Library::search(const SearchQuery& q) const
{
    std::vector<LibraryItem*> hits;
    for (const auto& item : items_)
    {
        if (!q.includeOnLoan() && item->getStatus() == ItemStatus::OnLoan) continue;

        if (auto* s = dynamic_cast<const Searchable*>(item.get()); s && s->matches(q.text()))
        {
            hits.push_back(item.get());
        }
    }
    return hits;
}

std::shared_ptr<Loan> Library::lend(const std::string& itemId, const std::string& memberId)
{
    Member* borrower = members_.findById(memberId);
    if (borrower == nullptr) return nullptr;

    for (const auto& item : items_)
    {
        if (item->getId() != itemId) continue;

        item->setStatus(ItemStatus::OnLoan);
        auto loan = std::make_shared<Loan>(std::shared_ptr<LibraryItem>(item.get(), [](LibraryItem*) {}),
                                           std::make_shared<Member>(*borrower),
                                           Date::today());
        loans_.push_back(loan);
        return loan;
    }
    return nullptr;
}

std::size_t Library::itemCount() const { return items_.size(); }

int Library::openCount() { return g_openCount; }

}  // namespace library
