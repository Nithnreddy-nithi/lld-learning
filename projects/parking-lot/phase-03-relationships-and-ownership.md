# Phase 03 — Relationships & Ownership

Object modeling is incomplete until we decide how objects relate.

## IS-A

Inheritance means one type can substitute for another.

~~~text
NearestSpotStrategy IS-A SpotAssignmentStrategy
~~~

Use inheritance for behavioral substitutability, not just taxonomy.

## HAS-A

### Composition

Strong conceptual ownership:

~~~text
ParkingLot ◆── ParkingFloor
ParkingFloor ◆── ParkingSpot
~~~

The lot contains floors; floors contain spots.

Important: composition in a class diagram does not automatically mean they must be one DDD aggregate or one DB transaction.

### Association

Ticket references a Vehicle and ParkingSpot, but does not own their lifecycle.

~~~text
Ticket ──> Vehicle
Ticket ──> ParkingSpot
Payment ──> Ticket
~~~

The spot existed before the ticket and remains after the ticket closes.

### Aggregation

Aggregation is weaker “has-a” ownership. In practical interviews, explain ownership clearly instead of obsessing over hollow-diamond notation.

## Dependency

A dependency means one object temporarily uses another.

Example:

~~~python
class ExitVehicleService:
    def __init__(self, pricing_strategy):
        self.pricing_strategy = pricing_strategy
~~~

The service depends on pricing behavior; pricing is not a child object in the domain.

## Unidirectional first

If Ticket needs Spot, keep:

~~~text
Ticket -> Spot
~~~

Do not automatically add:

~~~text
Spot -> current_ticket
~~~

unless a real use case needs the reverse reference. Bidirectional relationships create consistency work.

## Ownership questions

For every object ask:

- Who creates it?
- Who owns its lifecycle?
- Who may modify it?
- Who only reads it?
- Who should be allowed to transition its state?
- When can it be deleted or retired?

## Composition over inheritance

If behavior must vary independently, composition usually scales better:

~~~python
ParkingService(assignment_strategy=NearestSpotStrategy())
~~~

instead of creating:

~~~text
NearestSpotParkingService
LowestFloorParkingService
WeekendNearestSpotParkingService
...
~~~

## Key lesson

Relationships are not just arrows. They decide coupling, ownership, mutation rights, lifecycle, and how easily the model can change.
