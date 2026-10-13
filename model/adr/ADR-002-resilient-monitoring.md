# ADR-002 – Resilient Monitoring

The conceptual monitoring system should remain operational during
normal power or Internet failures.

The system conceptually uses:

- Battery backup during power failure.
- Cellular/SIM communication during normal Internet failure.

This allows monitoring and important communication to continue even
when normal cabin infrastructure is unavailable.

The static website only simulates this architecture.
