# 4 · Order and shipment

Two classes with a state machine each, and a class diagram that relates them. The
implementation contains **three deliberate mistakes** in the state machines, one of each kind
the report can find; the class diagram is implemented exactly.

**Result:** class diagram 100 % (26 elements) · `Order` 86.7 % (13 of 15 elements) ·
`Shipment` 81.2 % (13 of 16 elements).

| Mistake | In the report | File |
|---|---|---|
| The `pay` transition lost its guard `[hasItems]` | ✏️ Changed: 1, in `state-order-report.md` | [`order.hpp`](impl/include/shop/order.hpp) |
| `Paid --cancel / refund--> Cancelled` was left out | ➖ Missing: 1, in `state-order-report.md` | [`order.hpp`](impl/include/shop/order.hpp) |
| A state `Lost`, an event `lose` and a transition to it were added | ➕ Extra: 3, in `state-shipment-report.md` | [`shipment.hpp`](impl/include/shop/shipment.hpp) |

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `4-state-order`; you get three
reports in [`reports/`](reports/), one per design file.

## The mistakes

### ✏️ Changed — a guard was dropped

The design lets an order be paid only when it has items: `Created --pay [hasItems] / charge--> Paid`.
The row in `order.hpp` has `nullptr` where `&Order::hasItems` belongs. The class diagram is still
100 %, because `hasItems()` exists; it is just never consulted. Like the wrong ownership in
example 2, this compiles and runs. Only the state diagram shows it.

### ➖ Missing — a transition was left out

`Paid --cancel / refund--> Cancelled` has no row. An order that has been paid can no longer be
cancelled, and nobody is refunded. `refund()` exists, so the class diagram does not notice.

### ➕ Extra — a state was invented

`Shipment` has a state `Lost` and a transition `InTransit --lose--> Lost`. Sensible, perhaps,
but not designed. One invented state counts as **three** elements: the state, the event `lose`,
and the transition.

## Things to find

Open the comparisons from the top of each report and flip between the two pages:

- **Amber** on both pages of the `Order` comparison: the `pay` arrow. Hover over it to see
  *guard: hasItems → none*.
- **Red** on the design page: `cancel / refund` from `Paid`.
- **Green** on the implemented page of the `Shipment` comparison: `Lost`, in the column on the
  right, and the `lose` arrow routed to it.

The design also shows what the state-machine flow understands:

- **Two transitions on the same event**: `deliver [signed]` and `deliver [refused]` leave
  `In transit`; the guard tells them apart, so both are identified by their guard.
- **A self-transition**: `scan / log` on `In transit` is a row whose `from` and `to` are the
  same state.
- **Names**: the drawing says `In transit`, the code `InTransit`; the guard `[signed]` is
  implemented as `signed_()` because `signed` is a C++ keyword. Both are identical in the report.
- **The end symbol** after `Delivered` is documentation: a terminal state is one that no
  transition leaves, and the symbol is not counted.
- **One implementation, three reports**: the state machines and the class diagram share
  `impl/`, which is built once per run. In the class diagram `Order *-- "0..1" Shipment`:
  `dispatch()`, the action of `ship`, creates the shipment and sends it, one state machine
  driving another.

## Files

```
diagrams/input/class.drawio            the class diagram                          ← input
diagrams/input/state-order.drawio      the state machine of Order                 ← input
diagrams/input/state-shipment.drawio   the state machine of Shipment              ← input
impl/include/shop/*.hpp                the implementation's headers (compared)    ← input
impl/src/*.cpp                         the implementation's sources (built, not compared)
diagrams/output/                       generated: <design>-design.mmd, <design>-implemented.mmd,
                                                  <design>-comparison.drawio
reports/<design>-report.md             generated: the reports, one per design file
```

Every run deletes and regenerates the generated files, so don't edit them. How a state machine
maps to C++ is explained in
[UML-CPP-MAPPING.md](../../tools/umlverify/docs/UML-CPP-MAPPING.md#state-machines).
