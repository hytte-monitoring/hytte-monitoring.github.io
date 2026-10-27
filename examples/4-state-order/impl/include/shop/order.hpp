#pragma once

#include <optional>
#include <string>

#include "shop/shipment.hpp"

namespace shop {

class Order
{
public:
    // The states and events of diagrams/input/state-order.drawio.
    enum class State { Created, Paid, Shipped, Delivered, Cancelled };
    enum class Event { pay, ship, deliver, cancel };

    explicit Order(std::string id);

    void addItem();
    void handle(Event event);
    State state() const;

private:
    bool hasItems() const;   // guard
    void charge();           // actions
    void dispatch();
    void notify();
    void refund();

    std::string id_;
    int itemCount_ = 0;
    State state_ = State::Created;      // the initial state
    std::optional<Shipment> shipment_;  // composition 0..1: created by dispatch()

    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Order::*guard)() const;
        void (Order::*action)();
    };
    // MISTAKE 1 (changed): the design guards `pay` with [hasItems]; the guard was dropped.
    // MISTAKE 2 (missing): the design's `Paid --cancel / refund--> Cancelled` is not here.
    static constexpr Transition transitions[] = {
        {State::Created, Event::pay,     State::Paid,      nullptr, &Order::charge},
        {State::Paid,    Event::ship,    State::Shipped,   nullptr, &Order::dispatch},
        {State::Shipped, Event::deliver, State::Delivered, nullptr, &Order::notify},
        {State::Created, Event::cancel,  State::Cancelled, nullptr, nullptr},
    };
};

}  // namespace shop
