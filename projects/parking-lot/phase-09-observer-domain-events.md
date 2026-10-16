# Phase 09 — Observer / Domain Events

## The problem

When a spot changes from AVAILABLE to OCCUPIED, many things may react:

- display board
- analytics
- audit log
- mobile availability
- notifications

Bad design:

~~~python
class ParkingSpot:
    def assign_vehicle(self, vehicle):
        ...
        display_board.update(...)
        analytics.record(...)
        notifier.send(...)
        audit.write(...)
~~~

ParkingSpot now knows unrelated subsystems.

## Classic Observer

~~~python
class SpotObserver:
    def update(self, spot):
        raise NotImplementedError
~~~

Subject maintains subscribers and notifies them.

This reduces direct coupling but makes the subject own subscription mechanics.

## Domain-event style

A cleaner backend approach is to create an immutable event.

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class SpotOccupiedEvent:
    spot_id: str
    vehicle_plate: str


@dataclass(frozen=True)
class SpotReleasedEvent:
    spot_id: str
~~~

## Handlers

~~~python
class DisplayBoardHandler:
    def handle(self, event):
        ...


class AnalyticsHandler:
    def handle(self, event):
        ...


class AuditHandler:
    def handle(self, event):
        ...
~~~

## Event bus

~~~python
class EventBus:

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, handler):
        self._subscribers.setdefault(
            event_type,
            []
        ).append(handler)

    def publish(self, event):
        handlers = self._subscribers.get(
            type(event),
            []
        )

        for handler in handlers:
            handler.handle(event)
~~~

Registration:

~~~python
event_bus.subscribe(
    SpotOccupiedEvent,
    DisplayBoardHandler(),
)

event_bus.subscribe(
    SpotOccupiedEvent,
    AnalyticsHandler(),
)
~~~

## Publish after state change

Do not announce:

~~~text
SpotOccupied
~~~

before occupancy has actually changed.

State mutation first; event describes a fact that occurred.

## More domain-pure approach

Instead of injecting EventBus into ParkingSpot, entity can record events:

~~~python
class ParkingSpot:
    def __init__(...):
        self._events = []

    def assign_vehicle(self, vehicle):
        ...
        self._events.append(
            SpotOccupiedEvent(...)
        )

    def pull_events(self):
        events = list(self._events)
        self._events.clear()
        return events
~~~

Application service persists state and then routes recorded events.

## Command vs Event

Command:

~~~text
ParkVehicleCommand
= please attempt this
~~~

Event:

~~~text
VehicleParkedEvent
= this already happened
~~~

Commands may fail. Events represent facts.

## Synchronous vs asynchronous

In-process EventBus is synchronous.

For cross-process delivery you may use:

- Celery
- RabbitMQ
- Kafka
- SQS
- Redis Streams

But adding a broker creates delivery/retry/idempotency concerns.

## Event reliability

Consumers should tolerate duplicates. Handler failure policy matters. Ordering may matter. Domain events and integration events may have different payloads.

## Django signals

Signals are observer-like. They can be useful for secondary framework concerns, but hiding core business workflow in signals often makes behavior difficult to trace.

## Main lesson

Keep the critical use-case path explicit. Use events to decouple secondary reactions.
