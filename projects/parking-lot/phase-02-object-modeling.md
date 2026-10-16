# Phase 02 — Object Modeling

Core objects: ParkingLot, ParkingFloor, ParkingSpot, Vehicle, Ticket, Payment, EntryGate, ExitGate.

Enums: VehicleType, SpotType, TicketStatus, PaymentMethod, PaymentStatus.

```python
class ParkingSpot:
    def __init__(self, spot_id, spot_type):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.vehicle = None

    def is_available(self):
        return self.vehicle is None

    def assign_vehicle(self, vehicle):
        if not self.is_available():
            raise ValueError("Spot already occupied")
        self.vehicle = vehicle

    def release(self):
        self.vehicle = None
```

Avoid duplicated derived state. Vehicle can stay one class + enum until subclasses have real behavior differences.
