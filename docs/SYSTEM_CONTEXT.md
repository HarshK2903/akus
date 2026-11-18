# System context

See ARCHITECTURE.md for module ownership, implementation-plan.md for gates and
THREAT_MODEL.md for trust boundaries. Current Docker data is fictional LOCAL/DEMO.
Institutional Google OIDC, controlled identity linking, source administration and
effective authority are implemented and tested locally; live Google integration and
five-account UAT remain blocked on authorized external configuration and participation.
Google authenticates identity; approved institutional roster/offices authorize actions.
Provider metadata never establishes personal enrollment or certificates. PostgreSQL
is authoritative. No academic decision, quota or compliance service is simulated.
