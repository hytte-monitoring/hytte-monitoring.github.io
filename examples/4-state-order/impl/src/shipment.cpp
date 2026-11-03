#include "shop/shipment.hpp"

#include <iostream>
#include <utility>

namespace shop {

Shipment::Shipment(std::string trackingCode) : trackingCode_(std::move(trackingCode)) {}

void Shipment::sign(std::string name) { signature_ = std::move(name); }

void Shipment::refuse() { refused_ = true; }

void Shipment::handle(Event event)
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

Shipment::State Shipment::state() const { return state_; }

bool Shipment::signed_() const { return !signature_.empty(); }

bool Shipment::refused() const { return refused_; }

void Shipment::notify() { std::cout << "shipment " << trackingCode_ << ": on its way\n"; }

void Shipment::log() { std::cout << "shipment " << trackingCode_ << ": scanned\n"; }

}  // namespace shop
