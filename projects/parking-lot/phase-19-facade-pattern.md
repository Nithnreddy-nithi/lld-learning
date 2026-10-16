# Phase 19 — Facade Pattern + Application-Service Boundaries

## Problem

After splitting responsibilities we may have:

- PricingService
- PaymentService
- TicketService
- SpotService
- ReceiptService
- repositories

We do not want the controller coordinating all of them.

Without a boundary:

~~~text
Controller
  +-> PricingService
  +-> PaymentService
  +-> SpotService
  +-> TicketService
~~~

Now transport code knows subsystem workflow.

## Facade

A Facade gives one simple front door:

~~~text
Controller
    |
    v
ParkingFacade
    |
    +-> PricingService
    +-> PaymentService
    +-> SpotService
    +-> TicketService
~~~

## Example

~~~python
class ParkingFacade:

    def __init__(
        self,
        pricing_service,
        payment_service,
        ticket_service,
        spot_service,
    ):
        self.pricing_service = pricing_service
        self.payment_service = payment_service
        self.ticket_service = ticket_service
        self.spot_service = spot_service

    def exit_vehicle(
        self,
        ticket,
        spot,
        payment_method,
    ):
        amount = self.pricing_service.calculate(
            ticket
        )

        self.payment_service.pay(
            ticket,
            amount,
            payment_method,
        )

        self.spot_service.release(spot)
        self.ticket_service.close(ticket)

        return ExitResult(...)
~~~

## Flow

~~~text
POST /parking/exit
       |
       v
DRF View
       |
       v
ParkingFacade.exit_vehicle()
       |
       +--> PricingService.calculate()
       |
       +--> PaymentService.pay()
       |
       +--> SpotService.release()
       |
       +--> TicketService.close()
       |
       v
ExitResult
       |
       v
HTTP Response
~~~

## Important correction

Facade does **not** mean “move all code from a giant service into an even bigger Facade”.

The useful sequence is:

~~~text
big service knows too much
→ split focused responsibilities
→ caller now needs too much subsystem knowledge
→ optionally expose a facade
~~~

The Facade should mostly delegate.

## Facade vs Application Service

These can overlap.

Application Service:
- coordinates a business use case

Facade:
- simplifies access to a subsystem

An ExitVehicleService that already presents one clean entry point is already facade-like. Adding ParkingFacade around it may be pointless.

Do not create:

~~~text
Controller -> Facade -> Service -> another Service
~~~

when every layer only forwards arguments.

## Facade vs Adapter

Adapter:
- compatibility
- changes one interface into expected interface

Facade:
- simplification
- gives one high-level interface over many internals

## Facade vs Controller

Controller knows HTTP.

Facade/application service should remain independent of HTTP.

## God-object warning

Bad:

~~~text
ParkingFacade:
  park
  exit
  pricing implementation
  DB queries
  email
  reports
  users
  analytics
~~~

Good facade delegates to focused components.

## When it is useful

Use when:

- subsystem has many components
- callers repeatedly coordinate same services
- you want a stable public boundary
- internal structure should be hidden/refactorable

Do not use when it simply adds a redundant pass-through class.

## Interview definition

Facade provides a simplified, higher-level interface to a complex subsystem so callers do not need to depend on its internal components.
