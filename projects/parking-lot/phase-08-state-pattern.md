# Phase 08 — State Pattern

Ticket lifecycle:
```text
ACTIVE -> PAID -> CLOSED
   |
   -> LOST -> PAID -> CLOSED
```

```python
class TicketState:
    def pay(self, ticket): raise NotImplementedError
    def mark_lost(self, ticket): raise NotImplementedError
    def close(self, ticket): raise NotImplementedError

class Ticket:
    def __init__(self):
        self._state = ActiveTicketState()

    def pay(self):
        self._state.pay(self)

    def close(self):
        self._state.close(self)

    def change_state(self, state):
        self._state = state
```

Use full State Pattern only when enum + guarded methods becomes too conditional. App state does not solve DB concurrency.
