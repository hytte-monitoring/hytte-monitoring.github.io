#include <iostream>

#include "shop/order.hpp"
#include "shop/shipment.hpp"

namespace {

const char* name(shop::Order::State state)
{
    switch (state)
    {
        case shop::Order::State::Created: return "Created";
        case shop::Order::State::Paid: return "Paid";
        case shop::Order::State::Shipped: return "Shipped";
        case shop::Order::State::Delivered: return "Delivered";
        case shop::Order::State::Cancelled: return "Cancelled";
    }
    return "?";
}

const char* name(shop::Shipment::State state)
{
    switch (state)
    {
        case shop::Shipment::State::Pending: return "Pending";
        case shop::Shipment::State::InTransit: return "In transit";
        case shop::Shipment::State::Delivered: return "Delivered";
        case shop::Shipment::State::Returned: return "Returned";
        case shop::Shipment::State::Lost: return "Lost";
    }
    return "?";
}

}  // namespace

int main()
{
    shop::Order order("42");
    order.addItem();
    order.addItem();
    for (auto event : {shop::Order::Event::pay, shop::Order::Event::ship, shop::Order::Event::deliver})
    {
        order.handle(event);
        std::cout << "order: " << name(order.state()) << "\n";
    }

    shop::Shipment parcel("TRK-7");
    parcel.handle(shop::Shipment::Event::send);
    parcel.handle(shop::Shipment::Event::scan);
    parcel.sign("R. Receiver");
    parcel.handle(shop::Shipment::Event::deliver);
    std::cout << "parcel: " << name(parcel.state()) << "\n";
    return 0;
}
