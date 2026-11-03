#include "music/song.hpp"

#include <utility>

namespace music {

Song::Song(std::string title, int durationSeconds, const Artist* artist)
    : title_(std::move(title)), durationSeconds_(durationSeconds), artist_(artist)
{
}

std::string Song::getTitle() const { return title_; }

int Song::getDurationSeconds() const { return durationSeconds_; }

const Artist* Song::getArtist() const { return artist_; }

}  // namespace music
