# Phase 05 — Strategy Pattern: Spot Assignment

## The design pressure

The parking workflow is stable:

~~~text
receive vehicle
→ choose spot
→ assign vehicle
→ create ticket
~~~

But spot selection can vary:

- first available
- lowest floor
- nearest gate
- nearest elevator

A giant conditional makes the workflow change every time a new algorithm is added.

## Bad design

~~~python
def find_spot(vehicle, strategy):
    if strategy == "first":
        ...
    elif strategy == "nearest":
        ...
    elif strategy == "lowest_floor":
        ...
~~~

## Strategy contract

~~~python
from abc import ABC, abstractmethod

class SpotAssignmentStrategy(ABC):

    @abstractmethod
    def find_spot(self, parking_lot, vehicle):
        pass
~~~

Concrete algorithms:

~~~python
class FirstAvailableStrategy(SpotAssignmentStrategy):

    def find_spot(self, parking_lot, vehicle):
        for floor in parking_lot.floors:
            for spot in floor.spots:
                if spot.is_available() and spot.can_fit(vehicle):
                    return spot
        return None


class LowestFloorStrategy(SpotAssignmentStrategy):

    def find_spot(self, parking_lot, vehicle):
        for floor in sorted(parking_lot.floors, key=lambda f: f.floor_number):
            for spot in floor.spots:
                if spot.is_available() and spot.can_fit(vehicle):
                    return spot
        return None
~~~

## Context / application service

~~~python
class ParkVehicleService:

    def __init__(self, assignment_strategy):
        self.assignment_strategy = assignment_strategy

    def park_vehicle(self, parking_lot, vehicle):
        spot = self.assignment_strategy.find_spot(
            parking_lot,
            vehicle,
        )

        if spot is None:
            raise ParkingFullError()

        spot.assign_vehicle(vehicle)
        ...
~~~

## Dependency Injection

The service receives the strategy from outside:

~~~python
service = ParkVehicleService(
    assignment_strategy=NearestSpotStrategy()
)
~~~

The service does not construct its own concrete strategy.

## Strategy contract matters

A useful contract may say:

~~~text
find_spot()
- returns a compatible available spot
- or None
- must not assign/mutate the spot
~~~

If one implementation only selects while another secretly assigns the vehicle, callers cannot safely substitute them.

## Eligibility vs selection

These are different ideas:

~~~text
eligibility: is this spot valid for this vehicle?
selection: among valid spots, which one should we choose?
~~~

Keeping them distinct avoids mixing compatibility rules with ranking rules.

## Production reality

For 100,000 spots, do not load every spot into Python just to run a pattern. Push filtering/order into SQL where appropriate. A production strategy may collaborate with a repository/query object.

Pattern purity should never create terrible data access.

## Strategy vs similar patterns

- Strategy → how should an operation be performed?
- Factory → which concrete object should be created?
- State → behavior changes because lifecycle state changes.
- Adapter → translate incompatible interface.

## When not to use Strategy

Do not create a class hierarchy for simple values such as:

~~~python
RATE = {
    "bike": 20,
    "car": 40,
}
~~~

unless behavior genuinely varies.

## Interview definition

Strategy encapsulates interchangeable algorithms behind a common interface so the client can change the algorithm without changing the core workflow.
