# ADR-001 – Safety-Critical Monitoring Cannot Be Disabled

Safety-critical monitoring cannot be disabled or weakened by normal
user configuration.

This includes:

- Smoke monitoring being mandatory at all times.
- Internet/Connection monitoring being mandatory at all times.
- Indoor Temperature and Power becoming mandatory during cold-weather
  conditions.
- Critical thresholds being controlled by the system.
- Critical notifications overriding normal notification preferences.
- Immediate critical danger being able to override normal escalation
  restrictions.

The purpose is to prevent user configuration from making critical
safety functions ineffective.
