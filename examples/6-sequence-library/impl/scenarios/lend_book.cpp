// The scenario of diagrams/input/sequence-lend_book.drawio.
//
// main() sets the library up; scenario() makes the calls the diagram shows, and only those
// are recorded. The verifier runs this program in a traced build.
#include "lending/library.hpp"

namespace {

void scenario(lending::Library& library)
{
    library.lend("b1", "m1");   // Librarian -> Library : lend("b1", "m1")
}

}  // namespace

int main()
{
    lending::Library library;
    library.addBook("b1", "Dune");
    library.enrol("m1", "Ada");
    scenario(library);
    return 0;
}
