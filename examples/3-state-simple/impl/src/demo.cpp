#include <iostream>

#include "home/door.hpp"

namespace {

const char* name(home::Door::State state)
{
    switch (state)
    {
        case home::Door::State::Closed: return "Closed";
        case home::Door::State::Open: return "Open";
        case home::Door::State::Locked: return "Locked";
    }
    return "?";
}

}  // namespace

int main()
{
    using Event = home::Door::Event;
    home::Door door;
    std::cout << "start: " << name(door.state()) << "\n";
    for (auto [what, event] : {std::pair{"open", Event::open}, std::pair{"lock", Event::lock},
                               std::pair{"close", Event::close}, std::pair{"lock", Event::lock},
                               std::pair{"open", Event::open}, std::pair{"unlock", Event::unlock}})
    {
        door.handle(event);
        std::cout << what << " -> " << name(door.state()) << "\n";
    }
    return 0;
}
