# Phase 10 — Repository + Persistence

Repository abstracts persistence/query details when useful; service owns workflow.

```python
class TicketRepository:
    def get(self, ticket_id): ...
    def save(self, ticket): ...
```

Django ORM/Manager/QuerySet may be enough for simple CRUD.

Concurrency example:
```python
with transaction.atomic():
    spot = (
        ParkingSpot.objects
        .select_for_update(skip_locked=True)
        .filter(is_occupied=False)
        .first()
    )
```

Use short transaction boundaries. Repositories may hide locking details.
