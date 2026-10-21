# Parking Lot LLD — Complete Learning Notes

This project stores the full phase-by-phase Parking Lot LLD learning path. The goal is not to memorize patterns. The goal is to learn how to derive a design from requirements, protect invariants, handle real backend concerns, and explain the design in an interview.

## Design method

Use this order repeatedly:

Problem → real-world model → requirements → use cases → candidate objects → responsibilities → relationships → changing parts → abstractions/patterns → persistence → concurrency → reliability → performance → infrastructure.

For every object ask:

- What data belongs here?
- What behavior belongs here?
- Who owns it?
- Who creates it?
- Who modifies it?
- Who communicates with it?
- What happens when requirements change?

Patterns are introduced only when a concrete problem appears.

## Completed phases

1. Requirements and use cases
2. Object modeling
3. Relationships and ownership
4. Responsibilities and method placement
5. Strategy — spot assignment
6. Strategy — pricing
7. Payment + Factory
8. State Pattern
9. Observer / Domain Events
10. Repository + persistence
11. API / DRF mapping
12. Concurrency + idempotency
13. Transaction boundaries + failure recovery
14. Transactional Outbox
15. Value Objects
16. Aggregates + Aggregate Roots
17. Dependency Injection + object wiring
18. Adapter Pattern
19. Facade Pattern
20. Command Pattern
21. Builder Pattern
22. SOLID applied to Parking Lot
23. UML + design communication
24. Database schema design
25. Query design + performance
26. Caching + Redis
27. Background Jobs + Celery
28. Observability

Remaining phases continue from Phase 29.
