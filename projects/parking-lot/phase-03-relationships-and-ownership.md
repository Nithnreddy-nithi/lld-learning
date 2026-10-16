# Phase 03 — Relationships & Ownership

- IS-A → inheritance
- HAS-A → association/composition/aggregation
- Dependency → temporary use

Conceptual relationships:
- ParkingLot ◆→ ParkingFloor
- ParkingFloor ◆→ ParkingSpot
- Ticket → Vehicle
- Ticket → ParkingSpot
- Payment → Ticket

Prefer unidirectional relationships unless reverse navigation is useful. Composition does not automatically mean aggregate boundary. Ask who creates, owns, mutates, references, and retires each object.
