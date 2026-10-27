#include "music/artist.hpp"

#include <utility>

namespace music {

Artist::Artist(std::string name) : name_(std::move(name)) {}

std::string Artist::getName() const { return name_; }

}  // namespace music
