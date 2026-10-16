# Phase 16 — Aggregates & Aggregate Roots

## Why aggregates exist

As the domain grows, “who may mutate what?” becomes important.

An aggregate is a group of domain state treated as one consistency boundary.

The Aggregate Root is the entry point through which the aggregate is changed.

## Do not make a giant ParkingLot aggregate

Tempting:

~~~text
ParkingLot
  -> all floors
    -> all spots
      -> all tickets
        -> all payments
~~~

If every change required loading/locking this giant object, concurrency and performance would be terrible.

Rule:

> Choose the smallest aggregate boundary that can protect the invariant.

## Reasonable roots

For our design:

- ParkingSpot can be an aggregate/root for occupancy invariant.
- Ticket can be a root for parking-session lifecycle.
- Payment/PaymentAttempt can have its own lifecycle.
- ParkingLot may be configuration aggregate, depending on requirements.

## Ticket invariant

~~~python
class Ticket:

    def mark_paid(self):
        if self.status not in {
            TicketStatus.ACTIVE,
            TicketStatus.LOST,
        }:
            raise InvalidTransition()

        self.status = TicketStatus.PAID

    def close(self, exit_time):
        if self.status != TicketStatus.PAID:
            raise InvalidTransition(
                "Ticket must be paid before closing"
            )

        self.exit_time = exit_time
        self.status = TicketStatus.CLOSED
~~~

CLOSED implies exit_time exists.

## Cross-aggregate invariant

Exit needs:

~~~text
Ticket CLOSED
AND
Spot AVAILABLE
~~~

These can remain separate aggregates coordinated by an application service and one DB transaction.

Do not merge unrelated lifecycles merely because they participate in the same use case.

## Reference by identity

Instead of a huge mutable graph:

~~~python
ticket.spot.floor.parking_lot...
~~~

cross-aggregate references can often be IDs:

~~~text
ticket.parking_spot_id
~~~

This limits accidental mutation and loading.

## Repositories

Repositories generally operate around aggregate roots:

~~~text
TicketRepository
ParkingSpotRepository
PaymentRepository
~~~

## Cross-aggregate uniqueness

Example:

~~~text
only one open ticket per parking spot
~~~

Do not create one giant aggregate just to enforce it. Use:

- transaction
- lock/conditional update
- DB partial unique constraint

## Strong vs eventual consistency

Core invariants:

~~~text
spot allocation
ticket close + spot release
payment finalization
~~~

usually require strong local consistency.

Secondary effects:

~~~text
analytics
receipt
display refresh
~~~

may be eventual.

## Domain events

Aggregate can record domain events internally. Application layer persists aggregate changes and an outbox entry.

The aggregate should not publish Kafka messages directly.

## Read model

The aggregate shape does not need to match:

- DB schema
- API response
- dashboard query

A read endpoint may use an optimized SQL projection.

## Main lesson

Aggregate is a consistency boundary, not “everything connected in the class diagram.”
