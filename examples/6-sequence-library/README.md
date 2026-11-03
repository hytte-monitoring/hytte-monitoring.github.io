# 6 · Library lending, as scenarios

Five classes, a class diagram, and two scenarios drawn as sequence diagrams: *lend book* and
*return book*. The implementation contains **three deliberate mistakes** in the scenarios,
one of each kind the report can find; the class diagram is implemented exactly.

**Result:** class diagram 100 % (35 elements) · *lend book* 80.0 % (8 of 10 elements) ·
*return book* 77.8 % (7 of 9 elements).

| Mistake | In the report | File |
|---|---|---|
| `findMember()` is called after `markOnLoan()`, the design has it before | ✏️ Changed: 1, in `sequence-lend_book-report.md` | [`library.cpp`](impl/src/library.cpp) |
| A call to `Book::getTitle()` the design does not show | ➕ Extra: 1, in `sequence-lend_book-report.md` | [`library.cpp`](impl/src/library.cpp) |
| `Book::markReturned()` is never called | ➖ Missing: 2, in `sequence-return_book-report.md` | [`library.cpp`](impl/src/library.cpp) |

Run it with **Ctrl+Shift+B** (Cmd+Shift+B on macOS) and choose `6-sequence-library`; you get
three reports in [`reports/`](reports/), one per design file.

## How a scenario is verified

Nothing is read from the code this time. [`scenarios/lend_book.cpp`](impl/scenarios/lend_book.cpp)
is a program: `main()` sets a library up with one book and one member, then `scenario()` does
what the actor does in the drawing, `library.lend("b1", "m1")`. The verifier builds the
implementation a second time with every function instrumented, runs the program, and writes
down each call between the project's classes as it happens. Those calls, in order, are the
implemented sequence diagram; [`diagrams/output/sequence-lend_book-implemented.mmd`](diagrams/output/sequence-lend_book-implemented.mmd)
is what it recorded. The implementation contains no tracing code at all.

## The mistakes

### ✏️ Changed — a message moved

The design finds the member before it marks the book on loan. `lend()` in `library.cpp`
does it the other way round. The report says which message moved and what it follows on each
side; in the comparison the message is amber on both pages.

### ➕ Extra — an undesigned collaboration

`lend()` asks the book for its title to print a line. Harmless, but the design shows no such
message, and every call between classes counts. Draw it or drop it.

### ➖ Missing — a call left out

`giveBack()` removes the loan but never tells the book, so the book stays on loan for ever.
The message `Library → Book : markReturned()` is missing, and with it the `Book` lifeline:
nothing in the recorded scenario ever talks to a book. Both are red on the design page.

## Things to find

- **Grey** on the implemented page of *lend book*: `Library → Library : nextLoanId()`. The
  class calls its own private helper; the design does not draw it, so it is listed under
  *Not counted* and held against nothing. The self-message the design *does* draw,
  `findMember()`, is compared like any other.
- **Return arrows** (`book`, `true`) are documentation: drawn, never compared.
- **Set-up is invisible**: `main()` adds a book and enrols a member before `scenario()` runs,
  and none of those calls appear. In *return book*, `main()` even lends the book first.
- **Two scenarios, one implementation**: the same `library.cpp` serves both diagrams and the
  class diagram, and the whole project is built (twice) once per run.
- The class diagram shows `nextLoanId()` and `findMember()` as private methods, `Catalog` and
  `Loan` as compositions of `Library`, and `Loan` referring to its `Book` and `Member`.

## Files

```
diagrams/input/class.drawio                 the class diagram                       ← input
diagrams/input/sequence-lend_book.drawio    the scenario "lend book"                ← input
diagrams/input/sequence-return_book.drawio  the scenario "return book"              ← input
impl/include/lending/*.hpp                  the implementation's headers (compared)  ← input
impl/src/*.cpp                              the implementation's sources (built, not compared)
impl/scenarios/*.cpp                        one program per scenario (built, run, recorded)
diagrams/output/                            generated: <design>-design.mmd, <design>-implemented.mmd,
                                                       <design>-comparison.drawio
reports/<design>-report.md                  generated: the reports, one per design file
build-trace/                                the traced build and the recorded traces (not committed)
```

Every run deletes and regenerates the generated files, so don't edit them. How a scenario
maps to C++ is explained in
[UML-CPP-MAPPING.md](../../tools/umlverify/docs/UML-CPP-MAPPING.md#sequence-diagrams).
