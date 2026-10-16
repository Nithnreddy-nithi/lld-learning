# Phase 22 — SOLID Applied to the Parking Lot

SOLID is useful as a design-review tool, not as a class-count target.

## S — Single Responsibility Principle

A class should have one coherent reason to change.

Bad:

~~~python
class ParkingManager:
    def park(self):
        # DB query
        # select spot
        # pricing
        # payment
        # email
        # analytics
        # audit
        ...
~~~

This changes when any unrelated concern changes.

Better responsibilities:

~~~text
ParkingSpot -> occupancy/invariants
Ticket -> ticket lifecycle
ParkVehicleService -> entry workflow
ExitVehicleService -> exit workflow
PricingStrategy -> pricing policy
PaymentGatewayAdapter -> provider translation
Repository -> persistence
Event handlers -> secondary reactions
~~~

SRP does not mean “one method per class”. ParkingSpot can own several occupancy-related methods.

## O — Open/Closed Principle

Stable code should be extensible without repeatedly editing giant branches.

Bad:

~~~python
if strategy == "first":
    ...
elif strategy == "nearest":
    ...
elif strategy == "lowest":
    ...
~~~

Better:

~~~text
SpotAssignmentStrategy
  -> FirstAvailableStrategy
  -> NearestSpotStrategy
  -> LowestFloorStrategy
~~~

Adding NearestElevatorStrategy should not require rewriting ParkVehicleService.

OCP does not mean existing code can never change. Fundamental business changes may legitimately modify existing code.

## L — Liskov Substitution Principle

Every implementation must honor the abstraction's behavioral contract.

Suppose:

~~~python
class SpotAssignmentStrategy:
    def find_spot(...):
        """Return compatible available spot or None.
        Do not assign/mutate it."""
~~~

A strategy that secretly calls spot.assign_vehicle() violates caller expectations even if method signature matches.

Likewise PaymentGateway implementations should consistently return the application result semantics.

LSP is behavioral, not merely syntactic inheritance.

## I — Interface Segregation Principle

Clients should not depend on capabilities they do not use.

Bad:

~~~python
class PaymentGateway:
    def charge(...): ...
    def refund(...): ...
    def subscriptions(...): ...
    def payouts(...): ...
    def disputes(...): ...
~~~

If PaymentService only charges:

~~~python
class ChargeGateway(Protocol):
    def charge(self, payment_id, amount):
        ...


class RefundGateway(Protocol):
    def refund(self, payment_id, amount):
        ...
~~~

Split only when real clients need different capabilities. Do not create a one-method interface explosion automatically.

## D — Dependency Inversion Principle

High-level business workflow should not be tightly tied to low-level volatile details.

Bad:

~~~python
class PaymentService:
    def __init__(self):
        self.client = RazorpayClient(...)
~~~

Better:

~~~text
PaymentService
    ↓
PaymentGateway abstraction
    ↑
RazorpayAdapter
~~~

Similarly a service can depend on TicketRepository rather than hardcoding ORM details when that boundary creates value.

## DIP vs DI

DIP = design principle about dependency direction.

DI = mechanism to supply dependencies from outside.

## SOLID + patterns

Patterns often help satisfy design pressures:

- Strategy → OCP/DIP
- Adapter → SRP/DIP
- Repository → persistence separation/DIP
- State → state-specific responsibility
- Observer → extension of reactions
- Factory → creation separation
- DI → supports DIP

But patterns are not automatically required by SOLID.

## Five review questions

Instead of memorizing definitions, ask:

1. How many unrelated reasons can this class change?
2. Do new variants keep growing the same conditional?
3. Can implementations really substitute each other?
4. Does this client depend on methods it never uses?
5. Is business logic directly tied to volatile infrastructure?

## Main lesson

SOLID should make code clearer, more cohesive, testable, and easier to change. If applying SOLID creates dozens of meaningless abstractions, the design got worse.
