# Phase 09 — Observer / Domain Events

Secondary reactions to state changes: display, analytics, audit, notifications.

```python
@dataclass(frozen=True)
class SpotOccupiedEvent:
    spot_id: str
    vehicle_plate: str

class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, handler):
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event):
        for handler in self._subscribers.get(type(event), []):
            handler.handle(event)
```

Command = intent. Event = fact. Keep critical workflow explicit; use events for secondary reactions.
