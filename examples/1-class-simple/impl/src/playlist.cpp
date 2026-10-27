#include "music/playlist.hpp"

#include <utility>

namespace music {

Playlist::Playlist(std::string name) : name_(std::move(name)) {}

void Playlist::add(Song song) { songs_.push_back(std::move(song)); }

std::size_t Playlist::size() const { return songs_.size(); }

int Playlist::totalDurationSeconds() const
{
    int total = 0;
    for (const auto& song : songs_)
    {
        total += song.getDurationSeconds();
    }
    return total;
}

}  // namespace music
