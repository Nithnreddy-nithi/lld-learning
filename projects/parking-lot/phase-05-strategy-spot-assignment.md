# Phase 05 — Strategy Pattern: Spot Assignment

Variation: first available, lowest floor, nearest entrance, nearest elevator.

```python
from abc import ABC, abstractmethod

class SpotAssignmentStrategy(ABC):
    @abstractmethod
    def find_spot(self, parking_lot, vehicle):
        pass

class FirstAvailableStrategy(SpotAssignmentStrategy):
    def find_spot(self, parking_lot, vehicle):
        ...
```

Parking workflow depends on the strategy contract through dependency injection. Strategy selects; entity mutates. Do not use Strategy where a simple dict/config is enough.
