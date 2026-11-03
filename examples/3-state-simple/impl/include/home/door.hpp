#pragma once

namespace home {

class Door
{
public:
    // The states and events of diagrams/input/state-door.drawio.
    enum class State { Closed, Open, Locked };
    enum class Event { open, close, lock, unlock };

    void handle(Event event);
    State state() const;

private:
    State state_ = State::Closed;   // the initial state

    // The transition table: one row per arrow in the state diagram.
    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Door::*guard)() const;   // nullptr: no guard
        void (Door::*action)();        // nullptr: no action
    };
    static constexpr Transition transitions[] = {
        {State::Closed, Event::open,   State::Open,   nullptr, nullptr},
        {State::Open,   Event::close,  State::Closed, nullptr, nullptr},
        {State::Closed, Event::lock,   State::Locked, nullptr, nullptr},
        {State::Locked, Event::unlock, State::Closed, nullptr, nullptr},
    };
};

}  // namespace home
