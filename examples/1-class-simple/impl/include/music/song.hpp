#pragma once

#include <string>

#include "music/artist.hpp"

namespace music {

class Song
{
public:
    Song(std::string title, int durationSeconds, const Artist* artist);

    std::string getTitle() const;
    int getDurationSeconds() const;
    const Artist* getArtist() const;

private:
    std::string title_;
    int durationSeconds_ = 0;
    const Artist* artist_ = nullptr;   // raw pointer -> association: a song refers to its artist
};

}  // namespace music
