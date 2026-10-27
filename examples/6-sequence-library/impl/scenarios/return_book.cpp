// The scenario of diagrams/input/sequence-return_book.drawio.
#include "lending/library.hpp"

namespace {

void scenario(lending::Library& library)
{
    library.giveBack("b1");   // Librarian -> Library : giveBack("b1")
}

}  // namespace

int main()
{
    lending::Library library;
    library.addBook("b1", "Dune");
    library.enrol("m1", "Ada");
    library.lend("b1", "m1");   // set-up: the book is on loan before the scenario starts
    scenario(library);
    return 0;
}
