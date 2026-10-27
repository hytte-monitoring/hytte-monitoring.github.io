#include "library/member.hpp"

#include <utility>

namespace library {

Member::Member(std::string memberId, std::string name)
    : memberId_(std::move(memberId)), name_(std::move(name))
{
}

std::string Member::getName() const { return name_; }

std::string Member::getMemberId() const { return memberId_; }

}  // namespace library
