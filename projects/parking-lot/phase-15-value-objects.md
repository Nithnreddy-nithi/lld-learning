# Phase 15 — Value Objects

Value Objects have value equality and no independent identity.

```python
@dataclass(frozen=True)
class LicensePlate:
    value: str

    def __post_init__(self):
        normalized = self.value.strip().upper()
        if not normalized:
            raise ValueError("Plate required")
        object.__setattr__(self, "value", normalized)

@dataclass(frozen=True)
class Money:
    minor_units: int
    currency: str
```

Candidates: LicensePlate, Money, ParkingDuration, Address. Avoid float money. Do not make every primitive a class.
