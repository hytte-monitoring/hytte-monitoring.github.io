#include "lending/member.hpp"

#include <utility>

namespace lending {

Member::Member(std::string id, std::string name) : id_(std::move(id)), name_(std::move(name)) {}

std::string Member::getId() const { return id_; }

std::string Member::getName() const { return name_; }

}  // namespace lending
