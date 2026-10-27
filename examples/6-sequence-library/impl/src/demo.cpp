#include <iostream>

#include "lending/library.hpp"

int main()
{
    lending::Library library;
    library.addBook("b1", "Dune");
    library.addBook("b2", "Solaris");
    library.enrol("m1", "Ada");

    std::cout << "lend b1 to m1: " << (library.lend("b1", "m1") ? "ok" : "refused") << "\n";
    std::cout << "lend b1 again: " << (library.lend("b1", "m1") ? "ok" : "refused") << "\n";
    library.giveBack("b1");
    std::cout << "lend b1 after return: " << (library.lend("b1", "m1") ? "ok" : "refused") << "\n";
    return 0;
}
