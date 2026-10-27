#pragma once

// A minimal test helper: no framework to install. CHECK records a failure and
// continues; finish() prints a summary and returns the exit code for CTest.
#include <iostream>

namespace test {

inline int checks = 0;
inline int failures = 0;

inline void check(bool ok, const char* expr, const char* file, int line)
{
    ++checks;
    if (!ok)
    {
        ++failures;
        std::cerr << file << ":" << line << ": FAILED: " << expr << "\n";
    }
}

inline int finish(const char* suite)
{
    std::cout << suite << ": " << (checks - failures) << "/" << checks << " checks passed\n";
    return failures == 0 ? 0 : 1;
}

}  // namespace test

#define CHECK(expr) test::check((expr), #expr, __FILE__, __LINE__)
