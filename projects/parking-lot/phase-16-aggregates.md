# Phase 16 — Aggregates + Aggregate Roots

Aggregate = consistency boundary. Root controls mutation.

Avoid one giant ParkingLot aggregate. Reasonable roots: ParkingSpot, Ticket, Payment.

Cross-aggregate workflow can be coordinated by service + transaction; uniqueness/concurrency by locks/conditional updates/DB constraints.

Composition ownership is not automatically the aggregate boundary.
