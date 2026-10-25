# Phase 4, Concept 2 — Repository Pattern

## Goal

Expose persistence operations in domain language and keep SQL, ORM queries and row mapping outside application orchestration.

## Repository contracts

```python
from typing import Protocol
from uuid import UUID


class RecipientRepository(Protocol):
    def get_by_external_id(self, external_id: str) -> Recipient:
        ...


class TemplateRepository(Protocol):
    def get_active(
        self,
        template_key: str,
        channel: Channel,
    ) -> NotificationTemplate:
        ...


class DeliveryAttemptRepository(Protocol):
    def add(self, attempt: DeliveryAttempt) -> None:
        ...

    def update(self, attempt: DeliveryAttempt) -> None:
        ...

    def get(self, attempt_id: UUID) -> DeliveryAttempt:
        ...

    def list_for_request(
        self,
        request_id: UUID,
    ) -> tuple[DeliveryAttempt, ...]:
        ...
```

Contracts describe application needs instead of exposing a generic database API.

## Creation versus restoration

```python
@dataclass
class DeliveryAttempt:
    @classmethod
    def create(
        cls,
        request_id: UUID,
        recipient_id: str,
        channel: Channel,
        destination: str,
        now: datetime,
    ) -> "DeliveryAttempt":
        return cls(
            attempt_id=uuid4(),
            request_id=request_id,
            recipient_id=recipient_id,
            channel=channel,
            destination=destination,
            status=DeliveryStatus.PENDING,
            created_at=now,
            completed_at=None,
        )

    @classmethod
    def restore(cls, **persisted_values) -> "DeliveryAttempt":
        return cls(**persisted_values)
```

Loading an existing object must not generate new identity, timestamps or initial state.

## Row mapping

```python
def delivery_attempt_from_row(row) -> DeliveryAttempt:
    return DeliveryAttempt.restore(
        attempt_id=row["id"],
        request_id=row["request_id"],
        recipient_id=row["recipient_external_id"],
        channel=Channel(row["channel"]),
        destination=row["destination"],
        status=DeliveryStatus(row["status"]),
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )
```

Repositories return domain objects rather than raw dictionaries.

## SQL adapter sketch

```python
class PostgresDeliveryAttemptRepository:
    def __init__(self, connection) -> None:
        self._connection = connection

    def add(self, attempt: DeliveryAttempt) -> None:
        self._connection.execute(
            """
            INSERT INTO delivery_attempts (
                id, request_id, recipient_id, channel,
                destination, status, created_at, completed_at
            ) VALUES (
                %(id)s, %(request_id)s, %(recipient_id)s,
                %(channel)s, %(destination)s, %(status)s,
                %(created_at)s, %(completed_at)s
            )
            """,
            self._parameters(attempt),
        )
```

The exact database library may change; the domain-facing repository contract does not.

## Honest in-memory fake

```python
from copy import deepcopy


class InMemoryDeliveryAttemptRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, DeliveryAttempt] = {}

    def add(self, attempt: DeliveryAttempt) -> None:
        if attempt.attempt_id in self._items:
            raise ValueError("Attempt already exists")
        self._items[attempt.attempt_id] = deepcopy(attempt)

    def update(self, attempt: DeliveryAttempt) -> None:
        if attempt.attempt_id not in self._items:
            raise KeyError("Attempt does not exist")
        self._items[attempt.attempt_id] = deepcopy(attempt)
```

Copies prevent mutations outside the repository from silently changing stored state and hiding a missing `update()` call.

## Boundaries

A repository persists and reconstructs domain state. It should not render templates, call providers, choose retry policy or publish analytics. Repositories follow aggregate/use-case needs, not necessarily one repository per table.

## Exercise answers

1. Repositories return domain objects so behavior and types remain available.
2. `restore()` reconstructs persisted state without creation side effects.
3. Mutable shared references can make fake repositories unrealistically permissive.
4. SQL repositories need integration tests against a compatible real database.

## Takeaway

> Repositories translate between durable storage and domain objects without leaking storage mechanics into the workflow.


