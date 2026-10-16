# Phase 20 — Command Pattern + Use-Case Objects

## Starting point

A normal service call is fine:

~~~python
parking_service.park_vehicle(
    license_plate,
    vehicle_type,
    gate_id,
    user_id,
)
~~~

Command is not mandatory.

## Command idea

Represent the requested action as an object:

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class ParkVehicleCommand:
    license_plate: str
    vehicle_type: str
    gate_id: str
    user_id: str
    idempotency_key: str
~~~

A command means:

~~~text
Please perform this action.
~~~

## Handler

~~~python
class ParkVehicleCommandHandler:

    def __init__(
        self,
        spot_repository,
        ticket_repository,
        assignment_strategy,
    ):
        self.spot_repository = spot_repository
        self.ticket_repository = ticket_repository
        self.assignment_strategy = assignment_strategy

    def handle(self, command):
        ...
~~~

Usage:

~~~python
command = ParkVehicleCommand(
    license_plate="KA01AB1234",
    vehicle_type="car",
    gate_id="ENTRY-1",
    user_id="U1",
    idempotency_key="REQ-123",
)

result = handler.handle(command)
~~~

## Flow

~~~text
HTTP Request
    ↓
Serializer
    ↓
ParkVehicleCommand
    ↓
ParkVehicleCommandHandler
    ↓
Domain / Repository / Strategy
    ↓
ParkVehicleResult
    ↓
Response Serializer
~~~

## Why command objects help

They can make a complex request:

- explicit
- immutable
- loggable
- serializable
- queueable
- retryable
- auditable

They group use-case inputs rather than growing a long positional parameter list.

## Command vs Event

~~~text
ExitVehicleCommand
= attempt this action

VehicleExitedEvent
= the action already happened
~~~

Usually:

~~~text
Command -> one intended handler
Event   -> zero or many handlers
~~~

## Command Handler vs Application Service

These can be two architectural styles for the same role.

~~~python
class ExitVehicleService:
    def execute(...):
        ...
~~~

versus:

~~~python
class ExitVehicleCommandHandler:
    def handle(command):
        ...
~~~

Do not create both if they only forward calls.

## Command Result

~~~python
@dataclass(frozen=True)
class ParkVehicleResult:
    ticket_id: str
    spot_id: str
~~~

This keeps DRF Response out of the application layer.

## Command Bus

For many commands, a bus can dispatch based on command type:

~~~python
class CommandBus:

    def __init__(self):
        self._handlers = {}

    def register(self, command_type, handler):
        self._handlers[command_type] = handler

    def dispatch(self, command):
        handler = self._handlers[type(command)]
        return handler.handle(command)
~~~

Then:

~~~text
Command -> CommandBus -> matching Handler
~~~

A bus can later centralize logging, metrics, authorization, or transaction middleware.

For our medium Parking Lot this is optional and likely unnecessary initially.

## Queueing / retry

Commands may be serialized and queued, but queueing does not automatically make retries safe. Side-effecting commands still need idempotency.

## Undo

Classic GoF Command often teaches execute()/undo().

For backend business systems, generic undo is often wrong.

A successful charge is not undone by changing memory. Use explicit compensation:

~~~text
RefundPaymentCommand
~~~

## Command vs Query

Common convention:

~~~text
Command = changes state
Query   = returns data without changing state
~~~

This leads toward CQS/CQRS thinking without requiring full CQRS.

## Main lesson

Use Command when representing a use-case request as a first-class object creates real value. Do not add Command/Handler classes for trivial CRUD purely for ceremony.
