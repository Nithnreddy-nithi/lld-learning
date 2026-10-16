# Phase 23 — UML & Design Communication

The goal of UML in interviews is communication, not perfect notation.

## 1. Class Diagram

Answers:

~~~text
What objects exist?
What responsibilities do they have?
How are they related?
~~~

Core structure:

~~~text
ParkingLot 1
    |
    | 1..*
    v
ParkingFloor
    |
    | 1..*
    v
ParkingSpot -------- Vehicle
    ^
    |
    | historical 1..*
    |
ParkingTicket -------- PaymentAttempt
~~~

Conceptual composition:

~~~text
ParkingLot ◆── ParkingFloor
ParkingFloor ◆── ParkingSpot
~~~

Association:

~~~text
Ticket ──> Vehicle
Ticket ──> ParkingSpot
PaymentAttempt ──> Ticket
~~~

Inheritance/realization:

~~~text
NearestSpotStrategy
        |
        v
SpotAssignmentStrategy
~~~

Dependency:

~~~text
ParkVehicleService - - -> SpotAssignmentStrategy
~~~

## Cardinality

Useful notation:

- 1
- 0..1
- *
- 1..*

Example:

~~~text
Ticket 1 -> 0..* PaymentAttempt
~~~

Retries are why PaymentAttempt is many, not one.

## 2. Sequence Diagram

Answers:

~~~text
Who calls whom?
In what order?
~~~

Parking entry:

~~~text
Client
  -> API
  -> ParkVehicleService
  -> SpotRepository/Strategy
  -> PostgreSQL (find + lock)
  <- selected spot
  -> ParkingSpot.assign_vehicle()
  -> Ticket create
  -> save spot/ticket/outbox
  <- result
  <- HTTP 201
~~~

Exit:

~~~text
Client
 -> Exit API
 -> ExitVehicleService
 -> TicketRepository
 -> PricingStrategy
 -> PaymentService
 -> PaymentGateway Adapter
 -> External Provider
 <- result
 -> finalize Payment/Ticket/Spot
 -> Outbox
 <- ExitResult
~~~

## 3. State Diagram

Answers:

~~~text
How can one object's lifecycle change?
~~~

Ticket:

~~~text
ACTIVE --pay--> PAID --close--> CLOSED
   |
   +--mark_lost--> LOST --pay--> PAID
~~~

This makes illegal transitions clear.

Payment:

~~~text
PENDING -> PROCESSING -> SUCCESS
                     -> FAILED
                     -> UNKNOWN -> reconciliation
~~~

## 4. Component Diagram

Answers:

~~~text
How are larger architectural parts organized?
~~~

~~~text
Client
  ↓
DRF API
  ↓
Application Services
  ↓
Domain
  ↓
Repositories
  ↓
PostgreSQL

Application Service
  ↓
PaymentGateway
  ↓
RazorpayAdapter
  ↓
Razorpay

DB transaction
  ↓
Outbox
  ↓
Publisher
  ↓
Broker / Consumers
~~~

## Interview order

A strong LLD interview flow:

1. clarify requirements/scope
2. identify main workflows
3. identify core entities
4. assign responsibilities
5. draw core class relationships
6. discuss changing policies/patterns
7. trace one critical sequence
8. show lifecycle state if important
9. discuss persistence/concurrency
10. discuss extensions

Do not draw every serializer, getter, setter, manager, or framework type initially.

## Main lesson

Use the right diagram for the question:

~~~text
Class    -> WHAT exists?
Sequence -> WHO talks to whom and WHEN?
State    -> HOW lifecycle changes?
Component-> HOW larger pieces are organized?
~~~
