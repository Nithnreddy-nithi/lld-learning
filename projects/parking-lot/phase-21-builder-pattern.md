# Phase 21 — Builder Pattern + Complex Object Construction

## The problem

Simple constructors are best when construction is simple:

~~~python
ParkingLot(
    parking_lot_id="P1",
    name="Central Parking",
    address="Bengaluru",
)
~~~

As configuration grows:

~~~text
id
name
address
floors
entry gates
exit gates
display boards
pricing config
EV support
valet
operating hours
...
~~~

construction may become unreadable and multi-step.

Python keyword arguments already solve many constructor problems, so Builder must earn its complexity.

## Domain objects

~~~python
from dataclasses import dataclass
from enum import Enum

class SpotType(Enum):
    BIKE = "bike"
    COMPACT = "compact"
    LARGE = "large"


@dataclass(frozen=True)
class ParkingSpot:
    spot_id: str
    spot_type: SpotType


@dataclass(frozen=True)
class EntryGate:
    gate_id: str


@dataclass(frozen=True)
class ExitGate:
    gate_id: str


@dataclass(frozen=True)
class ParkingFloor:
    floor_number: int
    spots: tuple[ParkingSpot, ...]


@dataclass(frozen=True)
class ParkingLot:
    parking_lot_id: str
    name: str
    address: str
    floors: tuple[ParkingFloor, ...]
    entry_gates: tuple[EntryGate, ...]
    exit_gates: tuple[ExitGate, ...]
    supports_ev_charging: bool
    supports_valet: bool
~~~

## ParkingFloorBuilder

~~~python
class ParkingFloorBuilder:

    def __init__(self):
        self._floor_number = None
        self._spots = []

    def set_floor_number(self, floor_number):
        self._floor_number = floor_number
        return self

    def add_spot(self, spot_id, spot_type):
        self._spots.append(
            ParkingSpot(
                spot_id=spot_id,
                spot_type=spot_type,
            )
        )
        return self

    def build(self):
        if self._floor_number is None:
            raise ValueError(
                "Floor number is required"
            )

        if not self._spots:
            raise ValueError(
                "At least one spot is required"
            )

        return ParkingFloor(
            floor_number=self._floor_number,
            spots=tuple(self._spots),
        )
~~~

## ParkingLotBuilder

~~~python
class ParkingLotBuilder:

    def __init__(self):
        self._parking_lot_id = None
        self._name = None
        self._address = None
        self._floors = []
        self._entry_gates = []
        self._exit_gates = []
        self._supports_ev = False
        self._supports_valet = False

    def set_id(self, value):
        self._parking_lot_id = value
        return self

    def set_name(self, value):
        self._name = value
        return self

    def set_address(self, value):
        self._address = value
        return self

    def add_floor(self, floor):
        self._floors.append(floor)
        return self

    def add_entry_gate(self, gate_id):
        self._entry_gates.append(
            EntryGate(gate_id)
        )
        return self

    def add_exit_gate(self, gate_id):
        self._exit_gates.append(
            ExitGate(gate_id)
        )
        return self

    def enable_ev_charging(self):
        self._supports_ev = True
        return self

    def enable_valet(self):
        self._supports_valet = True
        return self

    def build(self):
        if not self._parking_lot_id:
            raise ValueError("ID required")

        if not self._name:
            raise ValueError("Name required")

        if not self._address:
            raise ValueError("Address required")

        if not self._floors:
            raise ValueError("At least one floor required")

        if not self._entry_gates:
            raise ValueError("Entry gate required")

        if not self._exit_gates:
            raise ValueError("Exit gate required")

        return ParkingLot(
            parking_lot_id=self._parking_lot_id,
            name=self._name,
            address=self._address,
            floors=tuple(self._floors),
            entry_gates=tuple(self._entry_gates),
            exit_gates=tuple(self._exit_gates),
            supports_ev_charging=self._supports_ev,
            supports_valet=self._supports_valet,
        )
~~~

## Usage

~~~python
floor1 = (
    ParkingFloorBuilder()
    .set_floor_number(1)
    .add_spot("F1-B1", SpotType.BIKE)
    .add_spot("F1-C1", SpotType.COMPACT)
    .add_spot("F1-L1", SpotType.LARGE)
    .build()
)

parking_lot = (
    ParkingLotBuilder()
    .set_id("P1")
    .set_name("Central Parking")
    .set_address("Bengaluru")
    .add_floor(floor1)
    .add_entry_gate("ENTRY-1")
    .add_exit_gate("EXIT-1")
    .enable_ev_charging()
    .build()
)
~~~

Each builder method returns self, enabling a fluent chain.

## Why build() exists

Builder may be incomplete during construction. Final product should be valid.

~~~text
Builder: mutable/incomplete construction state
build(): validate
Product: finished valid object
~~~

## Builder vs Factory

Factory:

~~~text
Which object/implementation should be created?
~~~

Builder:

~~~text
How should one complex object be assembled step by step?
~~~

They can collaborate: a factory can use a builder internally to create predefined configurations.

## Director

Classic GoF Builder may have a Director that defines construction steps. In Python, a normal function/factory often does the job more simply.

## When Builder is useful

- many optional parts
- multi-step construction
- object graph assembly
- cross-field construction validation
- immutable final product
- multiple predefined configurations

## When Builder is unnecessary

Do not create:

~~~text
MoneyBuilder
VehicleBuilder
TicketBuilder
~~~

when normal constructors/keyword arguments are clear.

## Main lesson

Use Builder for real construction complexity, not because it appears in the design-pattern catalog.
