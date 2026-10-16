# Phase 02 — Object Modeling

## Candidate objects

From the requirements we identify:

- ParkingLot
- ParkingFloor
- ParkingSpot
- Vehicle
- Ticket
- Payment
- EntryGate
- ExitGate

Supporting closed sets:

- VehicleType
- SpotType
- TicketStatus
- PaymentMethod
- PaymentStatus

## ParkingSpot

A spot has identity, type, and current occupancy.

~~~python
class ParkingSpot:
    def __init__(self, spot_id, spot_type):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.vehicle = None

    def is_available(self):
        return self.vehicle is None

    def assign_vehicle(self, vehicle):
        if not self.is_available():
            raise ValueError("Spot is already occupied")
        self.vehicle = vehicle

    def release(self):
        self.vehicle = None
~~~

Notice that we do not need both:

~~~python
self.vehicle = None
self.is_occupied = False
~~~

if one can be derived from the other. Two mutable representations can disagree.

## Vehicle

Initially a single Vehicle class is enough:

~~~python
class Vehicle:
    def __init__(self, license_plate, vehicle_type):
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type
~~~

Do not create Car, Bike, Truck subclasses merely because the nouns exist. Subclass when behavior genuinely differs.

## Ticket

Ticket represents a parking session.

Typical fields:

- ticket_id
- vehicle
- spot
- entry_time
- exit_time
- status

Ticket has lifecycle behavior, not just data.

## Payment

Keep Payment separate from Ticket because payment has its own lifecycle and may later have retries, provider references, refunds, failure reason, etc.

## Entity vs Value Object intuition

Entities have identity over time:

- Ticket T1001 remains T1001 even if status changes.
- ParkingSpot A101 remains A101.

Value objects are identified by value:

- Money(10000, INR)
- LicensePlate("KA01AB1234")

We introduce them formally later.

## Key lesson

Do not blindly convert every noun into a class. A class should exist because it has meaningful data, behavior, identity, lifecycle, or an abstraction role.
