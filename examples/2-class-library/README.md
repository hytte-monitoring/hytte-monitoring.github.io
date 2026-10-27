# 2 · Library lending system

An 11-class design with an implementation that contains **three deliberate mistakes**, one of
each kind the report can find. Everything else matches the design exactly.

**Result: 90.7 % alignment** — 68 of 75 elements identical.

| Mistake | In the report | File |
|---|---|---|
| The wrong kind of relation between `Loan` and `Member` | ✏️ Changed: 1 | [`loan.hpp`](impl/include/library/loan.hpp) |
| `Dvd.regionCode` was left out | ➖ Missing: 1 | [`dvd.hpp`](impl/include/library/dvd.hpp) |
| An unrequested `LoanValidator` class was added | ➕ Extra: 5 | [`loan_validator.hpp`](impl/include/library/loan_validator.hpp) |

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `2-class-library`, then open
[`reports/class-report.md`](reports/class-report.md).

## The mistakes

### ✏️ Changed — the wrong kind of ownership

The design draws `Loan --> Member : borrower`, an **association**: a loan *refers to* its
borrower. In C++ that is a raw pointer, `Member*`. The implementation uses
`std::shared_ptr<Member>`, which means "I am one of the owners". That is an **aggregation**.

This is the most important mistake of the three because **the code compiles and runs either
way**. No test fails and the compiler does not warn. The class diagram is the only place the
mistake shows. AI agents reach for `shared_ptr` by reflex.

### ➖ Missing — an attribute was left out

`Dvd` should have `-int regionCode`. It never made it into the header. This is the everyday
failure.

### ➕ Extra — an unrequested class was added

`LoanValidator` does not appear in the design. It is harmless and even sensible, which is the
point: *extra* is a difference, not necessarily a defect, and you decide whether it is wanted.
One invented class counts as **five** extra elements: the class, its attribute, its method, and
the two dependency arrows its method creates.

## Things to find

Open the comparison from the top of the report, then flip between the two pages:

- **Amber** on both pages: the `Loan → Member` arrow. It has an open arrowhead on the design page
  and a hollow diamond on the implemented page. Hover over it to see *association → aggregation*.
- **Red** on the design page: `Dvd.regionCode`.
- **Green** on the implemented page: the whole `LoanValidator` class, in the column on the right.
- **Grey** on the implemented page: `Library ..> Member`. The code has this dependency because
  `Library::enrol(Member m)` takes a `Member`. The design has the same method but no arrow, and
  designers rarely draw one, so it is **not counted**.

The design also shows most of what the verifier understands. Look for:

- an **interface** (`Searchable`), an **abstract** class (`LibraryItem`, name in italics), and an
  **enumeration** (`ItemStatus`)
- a generic class (`Catalog<T>`)
- all three ownership relations: **composition** (`Library` owns its items through
  `unique_ptr`), **aggregation** (`Loan.item`, through `shared_ptr`), and **association**
- cardinalities `1`, `0..1` (`returnedOn`, a `std::optional`) and `*`
- two relations between the same pair of classes (`Loan` to `Date`, as `dueDate` and
  `returnedOn`)

## Files

```
diagrams/input/class.drawio        the design                           ← input
impl/include/library/*.hpp         the implementation's headers (compared)  ← input
impl/src/*.cpp                     the implementation's sources (built, not compared)
diagrams/output/                   generated: class-design.mmd, class-implemented.mmd,
                                              class-comparison.drawio
reports/class-report.md            generated: the report
```

Every run deletes and regenerates the generated files, so don't edit them. How the C++ maps to
UML is explained in [UML-CPP-MAPPING.md](../../tools/umlverify/docs/UML-CPP-MAPPING.md).
