# Phase 10 — Repository Pattern + Persistence

## Why introduce persistence boundaries

Our domain objects started in memory. Real state must survive process restarts and concurrent requests.

A naive service may directly embed ORM queries everywhere:

~~~python
class ParkVehicleService:
    def execute(self, vehicle):
        spot = (
            ParkingSpotModel.objects
            .filter(...)
            .first()
        )
        ...
~~~

This is not automatically wrong in Django, but as persistence logic grows it can mix business workflow and database mechanics.

## Repository role

Repository exposes domain-oriented persistence operations.

~~~python
class SpotRepository:
    def get_available_for_update(self, vehicle_type):
        ...

    def save(self, spot):
        ...


class TicketRepository:
    def get(self, ticket_id):
        ...

    def add(self, ticket):
        ...

    def save(self, ticket):
        ...
~~~

The repository should not calculate parking fees, send emails, or process payments.

## Service vs Repository

~~~text
Service
= business use-case orchestration

Repository
= persistence/query boundary
~~~

## Django choices

### Style A — Django model as domain model

Pragmatic and common:

~~~text
APIView -> service -> Django Model/Manager/QuerySet
~~~

### Style B — separate domain + persistence model

More isolation:

~~~text
domain Ticket
<-> mapper/repository
<-> DjangoTicketModel
~~~

but more code.

For SDE1/machine coding, do not over-engineer if ORM models are sufficient.

## Race condition: last spot

Two requests can both read the same free spot unless the DB participates.

~~~python
from django.db import transaction

with transaction.atomic():
    spot = (
        ParkingSpot.objects
        .select_for_update(skip_locked=True)
        .filter(
            is_active=True,
            is_occupied=False,
        )
        .first()
    )

    if spot is None:
        raise ParkingFullError()

    spot.is_occupied = True
    spot.save(update_fields=["is_occupied"])
~~~

FOR UPDATE locks the chosen row. SKIP LOCKED allows another allocator to skip rows already claimed by another transaction.

## Transaction boundary

The use case, not each repository method independently, normally decides the transaction boundary.

~~~text
BEGIN
select/lock spot
update spot
insert ticket
COMMIT
~~~

## Optimistic alternative

Atomic conditional update:

~~~text
UPDATE spot
SET occupied = true
WHERE id = ? AND occupied = false
~~~

Check affected-row count.

## DB constraints

Application checks are not enough. Important invariants should also have DB protection where possible.

## Tests

Repository abstraction can make unit tests use FakeRepository while integration tests exercise real PostgreSQL behavior.

## Key lesson

Repository is useful when it creates a meaningful boundary. Django's ORM is already an abstraction, so do not create repository classes mechanically.
