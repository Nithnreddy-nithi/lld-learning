# Phase 17 — Dependency Injection & Object Wiring

## The problem

We now have many collaborators:

- repositories
- strategies
- pricing
- payment gateway
- event handlers
- clock
- services

Who creates and connects them?

Bad:

~~~python
class ParkingService:

    def __init__(self):
        self.ticket_repo = DjangoTicketRepository()
        self.spot_repo = DjangoSpotRepository()
        self.assignment = NearestSpotStrategy()
        self.gateway = RazorpayPaymentGateway(...)
~~~

The service decides all infrastructure and is hard to test/configure.

## Dependency Injection

Dependencies are supplied from outside.

~~~python
class ParkingService:

    def __init__(
        self,
        ticket_repo,
        spot_repo,
        assignment_strategy,
        payment_service,
    ):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo
        self.assignment_strategy = assignment_strategy
        self.payment_service = payment_service
~~~

Production:

~~~python
service = ParkingService(
    ticket_repo=DjangoTicketRepository(),
    spot_repo=DjangoSpotRepository(),
    assignment_strategy=NearestSpotStrategy(),
    payment_service=PaymentService(
        RazorpayPaymentGateway(...)
    ),
)
~~~

Tests:

~~~python
service = ParkingService(
    ticket_repo=FakeTicketRepository(),
    spot_repo=FakeSpotRepository(),
    assignment_strategy=FirstAvailableStrategy(),
    payment_service=PaymentService(
        FakePaymentGateway()
    ),
)
~~~

## Constructor injection

Best default for required dependencies because:

- dependencies are visible
- object cannot be created incomplete
- tests are straightforward

## Composition Root

Keep object creation/wiring in one explicit location.

~~~python
def build_parking_service():

    ticket_repo = DjangoTicketRepository()
    spot_repo = DjangoSpotRepository()

    gateway = RazorpayPaymentGateway(
        client=build_razorpay_client()
    )

    payment_service = PaymentService(
        gateway=gateway
    )

    assignment_strategy = (
        NearestSpotStrategy()
    )

    event_bus = EventBus()

    return ParkingService(
        ticket_repo=ticket_repo,
        spot_repo=spot_repo,
        assignment_strategy=assignment_strategy,
        payment_service=payment_service,
        event_bus=event_bus,
    )
~~~

Possible module:

~~~text
parking/bootstrap.py
~~~

## DIP vs DI

Dependency Inversion Principle:

~~~text
High-level policy should depend on stable abstractions, not volatile details.
~~~

Dependency Injection:

~~~text
Technique for supplying a dependency from outside.
~~~

You can inject a concrete type and still not fully follow DIP.

## Lifetimes

Think about object lifetime:

- application singleton
- per request
- per operation
- transient

A globally shared service must not store request-specific mutable state.

Bad:

~~~python
parking_service.current_ticket = ...
~~~

## Runtime strategy selection

Do not mutate one global service's strategy per request:

~~~python
parking_service.strategy = request_strategy
~~~

under concurrent requests.

Use a resolver/factory per operation or pass the strategy into the use case safely.

## Too many dependencies

A constructor with 15 dependencies can reveal that the service is too broad.

Split:

~~~text
ParkVehicleService
ExitVehicleService
~~~

rather than hiding dependencies in a “dependency bag”.

## Service Locator

Avoid:

~~~python
repo = container.get("ticket_repo")
~~~

inside business logic. This hides dependencies.

## Main lesson

DI makes architecture explicit: business code declares what it needs; composition root decides which concrete implementations satisfy those needs.
