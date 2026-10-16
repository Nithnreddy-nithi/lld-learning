# Phase 15 — Value Objects & Rich Domain Modeling

## Primitive obsession

A domain full of raw strings and ints loses meaning:

~~~python
vehicle_plate = " ka01ab1234 "
amount = 120.50
duration = 2
~~~

Important concepts can become Value Objects.

## Entity vs Value Object

Entity:
- identity matters
- state changes over time

Value Object:
- identified by its value
- usually immutable
- equality is value equality

~~~text
Ticket T1001 != Ticket T1002 even if fields match.
Money(10000, INR) == Money(10000, INR).
~~~

## LicensePlate

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class LicensePlate:
    value: str

    def __post_init__(self):
        normalized = self.value.strip().upper()

        if not normalized:
            raise ValueError("License plate is required")

        object.__setattr__(
            self,
            "value",
            normalized,
        )
~~~

Usage:

~~~python
Vehicle(
    license_plate=LicensePlate(" ka01ab1234 "),
    vehicle_type=VehicleType.CAR,
)
~~~

Now invalid/un-normalized plate values cannot spread throughout the domain.

## Money

~~~python
@dataclass(frozen=True)
class Money:
    minor_units: int
    currency: str

    def __post_init__(self):
        if self.minor_units < 0:
            raise ValueError("Money cannot be negative")

        normalized_currency = self.currency.upper()

        object.__setattr__(
            self,
            "currency",
            normalized_currency,
        )

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")

        return Money(
            self.minor_units + other.minor_units,
            self.currency,
        )
~~~

Prefer integer paise/cents or exact Decimal semantics; avoid binary float for money.

## ParkingDuration

~~~python
@dataclass(frozen=True)
class ParkingDuration:
    seconds: int

    @classmethod
    def between(cls, entry_time, exit_time):
        if exit_time < entry_time:
            raise ValueError("Invalid time range")

        return cls(
            int(
                (exit_time - entry_time)
                .total_seconds()
            )
        )

    @property
    def billable_hours(self):
        return max(
            1,
            math.ceil(self.seconds / 3600),
        )
~~~

Pricing becomes clearer:

~~~python
duration = ParkingDuration.between(
    ticket.entry_time,
    exit_time,
)

return Money(
    minor_units=duration.billable_hours * rate,
    currency="INR",
)
~~~

## Valid at construction

Prefer:

~~~python
plate = LicensePlate(raw)
~~~

to:

~~~python
plate = LicensePlate(raw)
plate.validate()
~~~

A value object should normally not exist in an invalid state.

## When to create a Value Object

Good signals:

- normalization
- validation
- domain behavior
- value equality
- units/currency
- meaning stronger than primitive type

Do not create UserNameValueObject, FloorNumberValueObject, etc. for every primitive unless they earn their complexity.

## Persistence

Value objects usually flatten into entity columns:

~~~text
amount_minor
currency
~~~

They rarely need their own table/repository.

## Main lesson

Value Objects make important domain concepts explicit, valid, immutable, and hard to misuse.
