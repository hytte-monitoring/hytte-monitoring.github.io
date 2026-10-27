#include <iostream>

#include "music/playlist.hpp"

int main()
{
    const music::Artist artist("Philip Glass");
    music::Playlist playlist("Focus");
    playlist.add(music::Song("Opening", 385, &artist));
    playlist.add(music::Song("Metamorphosis One", 312, &artist));

    std::cout << playlist.size() << " songs, " << playlist.totalDurationSeconds() << " seconds\n";
    return 0;
}
