#include "shop/order.hpp"

#include <iostream>
#include <utility>

namespace shop {

Order::Order(std::string id) : id_(std::move(id)) {}

void Order::addItem() { ++itemCount_; }

void Order::handle(Event event)
{
    for (const Transition& t : transitions)
    {
        if (t.from != state_ || t.event != event)
        {
            continue;
        }
        if (t.guard != nullptr && !(this->*t.guard)())
        {
            continue;
        }
        if (t.action != nullptr)
        {
            (this->*t.action)();
        }
        state_ = t.to;
        return;
    }
}

Order::State Order::state() const { return state_; }

bool Order::hasItems() const { return itemCount_ > 0; }

void Order::charge() { std::cout << "order " << id_ << ": charged for " << itemCount_ << " items\n"; }

void Order::dispatch()
{
    shipment_.emplace("TRK-" + id_);
    shipment_->handle(Shipment::Event::send);
}

void Order::notify() { std::cout << "order " << id_ << ": delivered\n"; }

void Order::refund() { std::cout << "order " << id_ << ": refunded\n"; }

}  // namespace shop
