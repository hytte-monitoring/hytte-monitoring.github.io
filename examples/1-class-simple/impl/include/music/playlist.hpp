#pragma once

#include <cstddef>
#include <string>
#include <vector>

#include "music/song.hpp"

namespace music {

class Playlist
{
public:
    explicit Playlist(std::string name);

    void add(Song song);
    std::size_t size() const;
    int totalDurationSeconds() const;

private:
    std::string name_;
    std::vector<Song> songs_;   // by value, many -> composition "*": the playlist owns its songs
};

}  // namespace music
