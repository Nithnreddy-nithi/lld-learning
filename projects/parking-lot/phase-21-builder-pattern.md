# Phase 21 — Builder Pattern

Builder constructs complex objects step by step.

```python
class ParkingLotBuilder:
    def __init__(self):
        self._id = None
        self._name = None
        self._floors = []

    def set_id(self, value):
        self._id = value
        return self

    def set_name(self, value):
        self._name = value
        return self

    def add_floor(self, floor):
        self._floors.append(floor)
        return self

    def build(self):
        if not self._id or not self._name or not self._floors:
            raise ValueError("Incomplete parking lot")
        return ParkingLot(self._id, self._name, tuple(self._floors))
```

Factory = which object?
Builder = how to assemble a complex object step-by-step?

Python keyword args/dataclasses reduce Builder need. Use it only for genuine construction complexity.
