#pragma once

#include <string>

namespace music {

class Artist
{
public:
    explicit Artist(std::string name);

    std::string getName() const;

private:
    std::string name_;
};

}  // namespace music
