#pragma once

#include <string>

namespace library {

class Member
{
public:
    Member(std::string memberId, std::string name);

    std::string getName() const;
    std::string getMemberId() const;

private:
    std::string memberId_;
    std::string name_;
};

}  // namespace library
