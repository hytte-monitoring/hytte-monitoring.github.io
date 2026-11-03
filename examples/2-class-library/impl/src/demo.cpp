#include <iostream>
#include <memory>

#include "library/book.hpp"
#include "library/dvd.hpp"
#include "library/library.hpp"

int main()
{
    library::Library lib("City Library");
    lib.enrol(library::Member("m-1", "Ada Lovelace"));
    lib.addItem(std::make_unique<library::Book>("i-1", "The Art of Computer Programming",
                                                "978-0201896831", 650));
    lib.addItem(std::make_unique<library::Dvd>("i-2", "Koyaanisqatsi", 86));

    std::cout << "items: " << lib.itemCount() << "\n";
    std::cout << "hits:  " << lib.search(library::SearchQuery("Computer", true)).size() << "\n";

    if (auto loan = lib.lend("i-1", "m-1"))
    {
        std::cout << "due:   " << loan->getDueDate().toIso() << "\n";
    }
    std::cout << "open:  " << library::Library::openCount() << "\n";
    return 0;
}
