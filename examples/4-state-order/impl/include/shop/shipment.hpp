#pragma once

#include <string>

namespace shop {

class Shipment
{
public:
    // The states and events of diagrams/input/state-shipment.drawio.
    // MISTAKE 3 (extra): the state Lost and the event lose are not in the design.
    enum class State { Pending, InTransit, Delivered, Returned, Lost };
    enum class Event { send, deliver, scan, lose };

    explicit Shipment(std::string trackingCode);

    void sign(std::string name);
    void refuse();
    void handle(Event event);
    State state() const;

private:
    bool signed_() const;   // guards (`signed` is a C++ keyword, hence the underscore)
    bool refused() const;
    void notify();          // actions
    void log();

    std::string trackingCode_;
    std::string signature_;
    bool refused_ = false;
    State state_ = State::Pending;   // the initial state

    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Shipment::*guard)() const;
        void (Shipment::*action)();
    };
    static constexpr Transition transitions[] = {
        {State::Pending,   Event::send,    State::InTransit, nullptr,            &Shipment::notify},
        {State::InTransit, Event::deliver, State::Delivered, &Shipment::signed_, nullptr},
        {State::InTransit, Event::deliver, State::Returned,  &Shipment::refused, nullptr},
        {State::InTransit, Event::scan,    State::InTransit, nullptr,            &Shipment::log},
        {State::Returned,  Event::send,    State::InTransit, nullptr,            &Shipment::notify},
        {State::InTransit, Event::lose,    State::Lost,      nullptr,            nullptr},   // extra
    };
};

}  // namespace shop
