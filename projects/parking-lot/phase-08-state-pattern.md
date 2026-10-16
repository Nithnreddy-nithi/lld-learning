# Phase 08 — State Pattern: Ticket Lifecycle

## Start simple

A ticket initially has lifecycle:

~~~text
ACTIVE -> PAID -> CLOSED
~~~

Lost-ticket requirement may add:

~~~text
ACTIVE -> LOST -> PAID -> CLOSED
~~~

For a small lifecycle, enum + guarded methods is often enough.

~~~python
class Ticket:
    def pay(self):
        if self.status not in {"active", "lost"}:
            raise InvalidTicketOperation()
        self.status = "paid"
~~~

## When full State Pattern helps

If each state supports different behavior and many methods contain repeated:

~~~python
if status == ...
elif status == ...
~~~

move behavior into state objects.

## State interface

~~~python
from abc import ABC, abstractmethod

class TicketState(ABC):

    @property
    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def pay(self, ticket):
        pass

    @abstractmethod
    def mark_lost(self, ticket):
        pass

    @abstractmethod
    def close(self, ticket):
        pass
~~~

## Concrete states

~~~python
class ActiveTicketState(TicketState):

    @property
    def status(self):
        return "active"

    def pay(self, ticket):
        ticket.change_state(PaidTicketState())

    def mark_lost(self, ticket):
        ticket.change_state(LostTicketState())

    def close(self, ticket):
        raise InvalidTicketOperation(
            "Active ticket cannot be closed"
        )


class LostTicketState(TicketState):

    @property
    def status(self):
        return "lost"

    def pay(self, ticket):
        ticket.change_state(PaidTicketState())

    def mark_lost(self, ticket):
        raise InvalidTicketOperation()

    def close(self, ticket):
        raise InvalidTicketOperation()


class PaidTicketState(TicketState):

    @property
    def status(self):
        return "paid"

    def pay(self, ticket):
        raise InvalidTicketOperation()

    def mark_lost(self, ticket):
        raise InvalidTicketOperation()

    def close(self, ticket):
        ticket.exit_time = datetime.now()
        ticket.change_state(ClosedTicketState())


class ClosedTicketState(TicketState):

    @property
    def status(self):
        return "closed"

    def pay(self, ticket):
        raise InvalidTicketOperation()

    def mark_lost(self, ticket):
        raise InvalidTicketOperation()

    def close(self, ticket):
        raise InvalidTicketOperation()
~~~

## Context

~~~python
class Ticket:

    def __init__(self, ticket_id, vehicle, spot):
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = datetime.now()
        self.exit_time = None
        self._state = ActiveTicketState()

    @property
    def status(self):
        return self._state.status

    def change_state(self, new_state):
        self._state = new_state

    def pay(self):
        self._state.pay(self)

    def mark_lost(self):
        self._state.mark_lost(self)

    def close(self):
        self._state.close(self)
~~~

## Strategy vs State

Strategy:
- client/application chooses algorithm
- behavior changes because algorithm choice changes

State:
- object behavior changes because internal lifecycle state changes
- state object may transition the context

## Persistence note

In the database you will usually persist a simple status value, not a Python state object graph.

## Concurrency note

State Pattern answers:

~~~text
Is this transition legal?
~~~

It does not answer:

~~~text
What if two requests transition the same DB row simultaneously?
~~~

That needs transactions, locks, versioning, or conditional updates.

## Main lesson

Use the simplest lifecycle model that remains clear. Upgrade from enum/guards to full State Pattern only when behavior genuinely becomes state-heavy.
