# Phase 23 — UML & Design Communication

Four useful views:

Class Diagram → what objects exist?
Sequence Diagram → who calls whom, in what order?
State Diagram → how lifecycle changes?
Component Diagram → how larger pieces are organized?

Core relationships:
```text
ParkingLot 1 -> * ParkingFloor
ParkingFloor 1 -> * ParkingSpot
ParkingSpot 1 -> * ParkingTicket (over time)
ParkingTicket 1 -> * PaymentAttempt
```

Entry sequence:
```text
Client -> API -> ParkVehicleService -> Strategy/Repo -> DB lock -> assign -> ticket -> save -> result
```

Communicate design decisions; avoid diagram noise.
