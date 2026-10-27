# UML ↔ C++ mapping contract

This is the single most important document in the repository. Two consumers must agree with it
exactly, or every report the tool produces is noise:

1. [`AGENTS.md`](../../../AGENTS.md), which tells the AI how to turn the design into C++
2. the extractors, [`class_diagram/cpp_extract.py`](../class_diagram/cpp_extract.py),
   [`state_diagram/cpp_extract.py`](../state_diagram/cpp_extract.py) and
   [`sequence_diagram/trace_extract.py`](../sequence_diagram/trace_extract.py) — how the
   verifier turns that C++ (or a run of it) back into the implemented design

If you change a rule here, change it in both, and re-run `tools/verify.py --all` to check the
examples still give the results their READMEs describe. Class diagrams come first, then
[state machines](#state-machines) and [sequence diagrams](#sequence-diagrams).

## Scope rules

- **The UML surface is headers only** — `impl/include/**/*.hpp`. Files under `impl/src/` are
  never read for diagram purposes.
- **Constructors, destructors and operator overloads are omitted** from diagrams.
- **A member that creates a relation is not also listed as an attribute.** Pick one: if
  `std::shared_ptr<Loan> loan_` becomes an aggregation edge, it does not also appear in the
  attribute compartment.
- **Primitives and standard value types are always attributes, never relations** — `int`,
  `double`, `bool`, `char`, `std::string`, `std::string_view`, and enums.
- Getters and setters are ordinary methods. They are not folded back into attributes.
- Trailing underscores on private members (`items_`) are stripped for the diagram (`items`).

## Visibility

| UML | C++ |
|---|---|
| `+` | `public:` |
| `#` | `protected:` |
| `-` | `private:` (the default for `class`) |
| `~` | not used in this project |

## Classifiers

| UML | C++ |
|---|---|
| `class` | `class` or `struct` with at least one data member |
| `<<abstract>>` | has at least one pure-virtual method (`= 0`) **and** at least one data member |
| `<<interface>>` | all methods pure virtual, **no** data members, has a virtual destructor |
| `<<enumeration>>` | `enum class` |
| generics | `template<typename T>` — rendered `Catalog~T~` |

An interface is therefore just an abstract class that carries no state. The distinction is made
mechanically, not by naming convention, so `IFoo` naming is neither required nor sufficient.

## Relations

Direction is always **from the owner to the owned/used type**.

| UML | C++ | Mermaid |
|---|---|---|
| inheritance | `class Derived : public Base` where `Base` has data members | `Base <|-- Derived` |
| realization | `class C : public I` where `I` is interface-shaped | `I <|.. C` |
| **composition** | `std::unique_ptr<T>` member, **or** a by-value `T` member | `Owner *-- T` |
| **aggregation** | `std::shared_ptr<T>` member | `Owner o-- T` |
| **association** | `T*`, `T&`, or `std::weak_ptr<T>` member | `Owner --> T` |
| dependency | `T` appears only in a parameter or return type — never as a member | `User ..> T` |

A dependency is only recorded when there is no stronger relation to the same type. Enums never
take part in relations.

Designers rarely draw a dependency arrow for every parameter type, so the verifier does not count
an implemented dependency as *extra* when the design already implies it through a method
signature. The report lists such arrows under **Not counted**.

Types used through a project template relate to the template: a `Catalog<Member>` member is a
relation to `Catalog`, not to `Member`. A template's own parameter (`T`) is never a relation.

The three ownership relations are the heart of the exercise. They are not stylistic: `unique_ptr`
means *this object's lifetime is mine*, `shared_ptr` means *shared, I am one of several owners*,
and a raw pointer means *I merely refer to it*. Getting these wrong is the most common and most
consequential error an AI makes when implementing a class diagram, and it compiles cleanly either
way.

## Multiplicity

A member says how many objects its class refers to, so it fixes the multiplicity at the **far
end** of the relation — the end of the class that is referred to:

| UML, far end | C++ |
|---|---|
| `1` | a single by-value, pointer or reference member |
| `0..1` | `std::optional<T>` |
| `*` | `std::vector<T>`, `std::map<K,T>`, `std::set<T>`, `std::list<T>` |

Multiplicity composes with ownership. `std::vector<std::unique_ptr<LibraryItem>>` is a
**composition with `*`**: `Library *-- "*" LibraryItem`. `std::vector<std::shared_ptr<Loan>>` is
an **aggregation with `*`**: `Library o-- "*" Loan`.

The **near end** ("how many `Loan`s point at one `Member`?") cannot be expressed by a member, so
the extractor never states it and the verifier does not compare it. A design may still show it —
for a composition the whole's end is `1` by definition, and `Loan --> Member` could honestly be
`*` to `1` — but it is documentation, not something the code can confirm.

## Drawing relations

How a relation is drawn, in draw.io and in the comparison:

- The **role name** is the member's name (`borrower_` → `borrower`) and the **multiplicity** is as
  above. Both go at the far end, on either side of the line, just outside the class.
- Every relation has an open **navigability arrowhead** at the far end, because a C++ member makes
  it one-way: the owner can reach the other class, not the reverse. Composition and aggregation
  keep their diamond at the owner's end as well.
- Inheritance and realization have a hollow triangle at the parent; dependency is dashed with an
  open arrowhead. None of these carry role names or multiplicities.

## Method and attribute modifiers

| UML | C++ |
|---|---|
| `$` (static) | `static` member |
| `*` (abstract) | pure virtual, `= 0` |
| `const` method | trailing `const` — recorded but not rendered in mermaid |
| `virtual` (non-pure) | recorded but not rendered |

## Type normalization

The diff normalizes types before comparing, so these are all equal:

| Written as | Normalizes to |
|---|---|
| `std::string`, `string` | `string` |
| `std::size_t`, `size_t`, `unsigned long` | `size_t` |
| `std::int32_t`, `int32_t`, `int` | `int` |
| `std::vector<T>`, `T[]` | `list<T>` |
| `std::unique_ptr<T>`, `std::shared_ptr<T>`, `T*`, `const T&` in a signature | `T` |
| `bool`, `boolean` | `bool` |
| `void` | `void` |

Names are matched case-insensitively with non-alphanumerics stripped, so `item_count`,
`itemCount` and `ItemCount` are the same member. This is deliberate: the exercise measures
*structure*, not naming style. A different word is a different name, though: `getItemCount` is
not `itemCount`.

## Worked reference

`examples/2-class-library/` implements every class-diagram rule on this page. When in doubt, read
`examples/2-class-library/impl/include/library/` next to
`examples/2-class-library/diagrams/output/class-design.mmd`. For state machines, read
`examples/4-state-order/impl/include/shop/` next to its `diagrams/output/state-*-design.mmd`.

## State machines

A state machine drawn for a class — `diagrams/input/state-<class>.drawio`, the file named after
the class in lower case, `state-library_item.drawio` for `LibraryItem` — is implemented
**table-driven, inside that class**. The drawing is the table; `handle()` merely runs it.

| UML | C++ |
|---|---|
| the states | `enum class State { … }` nested in the class, one enumerator per state, in drawing order |
| the events on the transitions | `enum class Event { … }` nested in the class, one enumerator per event |
| a guard, `[hasKey]` | a private `bool hasKey() const` member function |
| an action, `/ log` | a private `void log()` member function |
| the transitions | `static constexpr Transition transitions[]`: one row per arrow, `{from, event, to, guard, action}`, `nullptr` for no guard or no action |
| the initial transition, `[*] --> Closed` | the state attribute's default member initializer, `State state_ = State::Closed;` |
| firing an event | `void handle(Event)`: the row for the current state and event whose guard holds runs its action and enters its target; an event with no row is ignored |
| a state with no outgoing arrows (or an arrow to the end symbol) | nothing extra: a terminal state is one that no row leaves |

The row type is declared in the class, before the table:

```cpp
class Door
{
public:
    enum class State { Closed, Open, Locked };
    enum class Event { open, close, lock, unlock };

    void handle(Event event);
    State state() const;

private:
    bool hasKey() const;   // guard
    void log();            // action

    State state_ = State::Closed;   // the initial state

    struct Transition
    {
        State from;
        Event event;
        State to;
        bool (Door::*guard)() const;   // nullptr: no guard
        void (Door::*action)();        // nullptr: no action
    };
    static constexpr Transition transitions[] = {
        {State::Closed, Event::open,   State::Open,   nullptr,       nullptr},
        {State::Closed, Event::lock,   State::Locked, &Door::hasKey, &Door::log},
        …
    };
};
```

- Every row lists **all five fields**. A row may not leave trailing fields out: the build must
  stay warning-free, and `-Wextra` warns about missing field initializers.
- The table comes **after** the guards and actions it names: a static member's initializer can
  only refer to members already declared.
- One guard and one action per transition. `[a and b]` is one method that checks both;
  `/ x, y` is one method that does both. No `[else]` and no `[!inStock]`: write a named guard,
  `[outOfStock]`.
- Composite states, entry/exit actions, history and choice pseudo-states are not part of the
  mapping; the verifier warns when a drawing uses them.

**In the class diagram**, `State`, `Event`, `Transition` and `transitions` belong to the state
machine and are not class-diagram elements: nested types and static tables are not extracted.
The class box shows the attribute `- state: State`, the method `+ handle(event: Event): void`,
and the guard and action methods like any other methods.

**What the extractor reads back**: the table's rows, with each field's role taken from its type
(the two fields of one enum are `from` and `to`, in that order; the field of the other enum is the
event; a member-function pointer returning `bool` is the guard and one returning `void` the
action); the states from the State enum, in declaration order; the events the table uses (a
declared but unused enumerator is a warning); the initial state from the initializer. A
`std::array<Transition, N>` is read like a C array.

**Names** compare as everywhere on this page: `In transit` ≡ `InTransit` ≡ `in_transit`, and a
trailing underscore is ignored, so the guard `[signed]` may be `signed_()` because `signed` is a
C++ keyword.

## Sequence diagrams

A sequence diagram, `diagrams/input/sequence-<scenario>.drawio`, is one scenario: what the
objects say to each other when the actor does one thing. It is implemented as a small program
that *does* that thing, and verified by running it: the calls between the project's classes,
in order, are the messages. Nothing is read from the code; it is recorded from a run.

| UML | C++ |
|---|---|
| the scenario | `impl/scenarios/<scenario>.cpp`, built by `add_executable(scenario_<scenario> scenarios/<scenario>.cpp)` and linked to the library |
| the set-up the diagram does not show | `main()`: it creates the objects, then calls `scenario()` |
| the actor's messages | the calls `scenario()` makes: `void scenario(Library& library) { library.lend("b1", "m1"); }` |
| a lifeline `order: Order` | an object of class `Order` — one per class |
| a message `Library → Catalog : find(id)` | `Catalog::find` entered while `Library::lend` runs: a call of one class's method from another's |
| a self-message `Library → Library : findMember(id)` | a call of the class's own method — drawn when it matters, otherwise not counted |
| a return message (dashed) | the return of the call; documentation, not compared |

The rules the recording follows:

- **A message is a method call between the project's classes.** Its receiver is the object's
  actual class, whatever pointer or reference type it was called through. Its caller is the
  class whose method made the call — code in a lambda belongs to the method it is written in.
  Calls from `scenario()` itself, or from any function that is not a class method, come from
  the actor.
- **Constructors, destructors, operators and free functions are never messages**, nor are calls
  into the standard library. A creation message in a drawing (`«create»`) is a warning.
- **Every call between classes counts**, getters included. A call a class makes to itself is
  counted only if the design draws it.
- **Order is compared, arguments are not.** `lend("b1", "m1")` and `lend(bookId, memberId)`
  are the same message; only the method name matters.
- **The scenario must be deterministic**: single-threaded, no clock, no randomness, no input.
  The same program must make the same calls every time.
- **Objects are told apart by class.** Two lifelines of one class in a diagram are a warning.

Fragments (`alt`, `loop`, `opt`) are not supported: one run takes one path, so draw one
scenario per path.
