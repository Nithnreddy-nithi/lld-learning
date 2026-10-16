# Phase 04 — Responsibilities & Method Placement

Put behavior near the data and invariants it protects.

ParkingSpot owns: is_available, can_fit, assign_vehicle, release.
Ticket owns lifecycle transitions.
Application service coordinates cross-object workflow.

```python
class ParkVehicleService:
    def park_vehicle(self, vehicle):
        spot = self.assignment_strategy.find_spot(vehicle)
        if not spot:
            raise ParkingFullError()
        spot.assign_vehicle(vehicle)
        return Ticket.create(vehicle, spot)
```

Service = conductor; entities/policies = musicians.
