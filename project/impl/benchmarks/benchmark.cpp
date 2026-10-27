// Host benchmarks (Phase 3, spec §7.3): the average time of the model's hot paths.
// Build in Release: cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
#include <chrono>
#include <iostream>
#include <memory>

#include "hytte/cabin.hpp"
#include "hytte/emergency_contact.hpp"
#include "hytte/incident.hpp"
#include "hytte/incident_history.hpp"
#include "hytte/monitoring_system.hpp"

namespace {

constexpr int kRuns = 1'000'000;

template <typename Work>
double nanosecondsPerRun(Work work)
{
    auto start = std::chrono::steady_clock::now();
    for (int i = 0; i < kRuns; ++i)
    {
        work();
    }
    std::chrono::duration<double, std::nano> total = std::chrono::steady_clock::now() - start;
    return total.count() / kRuns;
}

}  // namespace

int main()
{
    using Event = hytte::Incident::Event;

    // One full Incident lifecycle: New -> Warning -> Critical -> Closed (3 transitions).
    double lifecycle = nanosecondsPerRun([] {
        hytte::Incident incident("I-1", "2026-10-27T12:00");
        incident.handle(Event::warningDetected);
        incident.handle(Event::conditionWorsens);
        incident.handle(Event::ownerResolved);
    });

    // The smoke_escalation scenario: evaluate, create, register, escalate, notify, update.
    hytte::Cabin cabin("c1", "Hytte");
    hytte::IncidentHistory history;
    auto contact = std::make_shared<hytte::EmergencyContact>("e1", "Family member", "+47 000 00 000");
    hytte::MonitoringSystem system(cabin, history, {contact});
    double evaluate = nanosecondsPerRun([&] { system.evaluateEvent(); });

    std::cout << "runs per measurement: " << kRuns << "\n"
              << "incident lifecycle (3 x handle): " << lifecycle << " ns\n"
              << "MonitoringSystem::evaluateEvent(): " << evaluate << " ns\n";
    return 0;
}
