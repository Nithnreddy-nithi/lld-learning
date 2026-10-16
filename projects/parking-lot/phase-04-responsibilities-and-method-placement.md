# Phase 04 — Responsibilities & Method Placement

## Main question

Once objects exist, where should behavior live?

Use these tests:

- Who has the information?
- Whose state changes?
- Is this intrinsic domain behavior or cross-object workflow?
- Is this a policy that may vary?
- Will placing it here improve cohesion?

## ParkingSpot responsibility

ParkingSpot owns its own occupancy invariant.

~~~python
class ParkingSpot:
    def is_available(self):
        return self.vehicle is None

    def can_fit(self, vehicle):
        ...

    def assign_vehicle(self, vehicle):
        if not self.is_available():
            raise SpotOccupiedError()

        if not self.can_fit(vehicle):
            raise IncompatibleSpotError()

        self.vehicle = vehicle

    def release(self):
        if self.vehicle is None:
            raise SpotAlreadyFreeError()

        self.vehicle = None
~~~

Outside code should not do:

~~~python
spot.vehicle = vehicle
~~~

because that bypasses invariants.

## Ticket responsibility

Ticket owns legal ticket transitions:

~~~python
ticket.mark_paid()
ticket.mark_lost()
ticket.close(exit_time)
~~~

The service should not directly write:

~~~python
ticket.status = "closed"
~~~

## Application service responsibility

A service coordinates a use case across objects:

~~~python
class ParkVehicleService:
    def __init__(self, assignment_strategy, ticket_repository, spot_repository):
        self.assignment_strategy = assignment_strategy
        self.ticket_repository = ticket_repository
        self.spot_repository = spot_repository

    def park_vehicle(self, vehicle):
        spot = self.assignment_strategy.find_spot(vehicle)

        if spot is None:
            raise ParkingFullError()

        spot.assign_vehicle(vehicle)

        ticket = Ticket.create(
            vehicle=vehicle,
            spot=spot,
        )

        self.spot_repository.save(spot)
        self.ticket_repository.add(ticket)

        return ticket
~~~

The service is the conductor. Domain entities and policies do the specialized work.

## Pricing does not belong in Vehicle

Vehicle may contain its type, but pricing changes for reasons unrelated to Vehicle:

- weekend
- event
- VIP
- lost ticket
- surge

So pricing is a separate policy.

## Information Expert

Put behavior with the object that has the required information, as long as doing so does not create unrelated responsibilities.

## Tell, Don't Ask

Prefer:

~~~python
spot.assign_vehicle(vehicle)
~~~

to:

~~~python
if spot.vehicle is None and ...:
    spot.vehicle = vehicle
~~~

## SRP correctly understood

Single Responsibility does not mean one method per class. It means one coherent reason to change.

ParkingSpot may legitimately have several occupancy-related methods because they belong to one responsibility.

## Key lesson

Entities protect their state. Application services coordinate multiple participants. Policies encapsulate changing business decisions.
