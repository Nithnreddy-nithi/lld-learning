# Phase 20 — Command Pattern

Command represents a requested action.

```python
@dataclass(frozen=True)
class ParkVehicleCommand:
    license_plate: str
    vehicle_type: str
    gate_id: str
    idempotency_key: str

class ParkVehicleCommandHandler:
    def handle(self, command):
        ...
```

Flow: HTTP -> Serializer -> Command -> Handler -> Domain/Repository -> Result.

Command = intent; Event = fact. Commands can help with logging, queueing, retrying, auditing, and explicit use-case boundaries.
