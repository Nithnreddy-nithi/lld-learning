# Phase 01 — Requirements & Use Cases

## Why this phase exists

The first mistake in LLD is jumping directly to classes. A good design starts with the real-world workflow and scope. If requirements are unclear, class design becomes guesswork.

## Initial requirements

The first version contains one ParkingLot with multiple ParkingFloors and ParkingSpots.

Vehicle types:

- BIKE
- CAR
- TRUCK

Spot types:

- BIKE
- COMPACT
- LARGE

Initial compatibility:

- Bike → BIKE, COMPACT, LARGE
- Car → COMPACT, LARGE
- Truck → LARGE

Entry flow:

1. Vehicle arrives at entry gate.
2. Find a compatible available spot.
3. Reserve/assign that spot.
4. Create a ticket.
5. Return ticket and spot information.

Exit flow:

1. Receive ticket.
2. Determine exit time.
3. Calculate fee.
4. Process payment.
5. Mark payment successful.
6. Release the parking spot.
7. Close the ticket.
8. Open exit gate / return result.

Initial pricing:

- Bike: ₹20/hour
- Car: ₹40/hour
- Truck: ₹60/hour
- Partial hours round up.

Parking-full must be an explicit business error.

## Out of scope initially

Do not design everything at once. Initially exclude:

- reservations
- monthly subscriptions
- valet
- EV charging
- cameras
- VIP
- dynamic pricing
- discounts
- lost-ticket handling

Some are introduced later to test extensibility.

## Main use cases

- ParkVehicle
- FindSpot
- GenerateTicket
- CalculateFee
- ProcessPayment
- ExitVehicle
- ReleaseSpot
- GetAvailability

## The six questions to ask for any LLD

1. What must the system do?
2. Who interacts with it?
3. What are the important workflows?
4. What objects exist?
5. What responsibility belongs to each object?
6. What part is likely to vary?

These questions are reusable for ATM, Elevator, Cricbuzz, Splitwise, Library, Movie Booking, etc.

## Key lesson

Do not start from “ParkingLot class, Floor class, Spot class...”.

Start from:

~~~text
Vehicle arrives
→ spot must be found safely
→ spot becomes occupied
→ ticket is created
→ later fee is calculated
→ payment succeeds
→ spot becomes free
~~~

Classes should emerge from the workflow.
