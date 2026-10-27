#pragma once

#include <string>

namespace lending {

class Member
{
public:
    Member(std::string id, std::string name);

    std::string getId() const;
    std::string getName() const;

private:
    std::string id_;
    std::string name_;
};

}  // namespace lending
