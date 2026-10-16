# Phase 06 — Pricing Strategy

Spot assignment showed one variation axis. Pricing is another.

## Why pricing should be isolated

Initial rates are simple:

- Bike ₹20/hour
- Car ₹40/hour
- Truck ₹60/hour

Later requirements may introduce:

- weekend rates
- event pricing
- lost-ticket fee
- VIP discount
- surge pricing

If all of this enters ExitVehicleService as conditionals, that service becomes unstable.

## Contract

~~~python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):

    @abstractmethod
    def calculate_fee(self, ticket, exit_time):
        pass
~~~

## Hourly pricing

~~~python
import math

class HourlyPricingStrategy(PricingStrategy):

    def __init__(self, rates):
        self.rates = rates

    def calculate_fee(self, ticket, exit_time):
        seconds = (exit_time - ticket.entry_time).total_seconds()
        hours = max(1, math.ceil(seconds / 3600))

        rate = self.rates[ticket.vehicle.vehicle_type]

        return Money(
            minor_units=hours * rate * 100,
            currency="INR",
        )
~~~

## Alternative strategies

~~~python
class WeekendPricingStrategy(PricingStrategy):
    def calculate_fee(self, ticket, exit_time):
        ...


class LostTicketPricingStrategy(PricingStrategy):
    def calculate_fee(self, ticket, exit_time):
        ...
~~~

## Exit flow

~~~text
ExitVehicleService
    |
    +--> PricingStrategy.calculate_fee()
    |
    +--> PaymentService
    |
    +--> Ticket/Spot finalization
~~~

The service does not care which concrete pricing algorithm was injected.

## Composition for independent rules

Be careful with class explosion:

~~~text
WeekendVipLostTicketStrategy
WeekendVipNormalStrategy
WeekdayVipStrategy
...
~~~

If discounts are independent modifiers, composition/decorator-style policies may be better than one strategy for every combination.

## Prefer Money

Pricing should not return float:

~~~python
120.1
~~~

Use an explicit Money value object with integer minor units or exact decimal semantics.

## Pure-ish policy

Pricing is easier to test if it behaves like:

~~~text
ticket data + exit time -> Money
~~~

and does not also save DB rows, send receipts, and call external services.

## Main lesson

Stable workflow stays in the application service. Changing pricing policy lives behind a pricing abstraction.
