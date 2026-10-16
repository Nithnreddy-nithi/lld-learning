# Phase 11 — API / DRF Mapping

## Overall flow

~~~text
Client
  ↓
DRF View
  ↓
Serializer
  ↓
Application Service / Command Handler
  ↓
Domain / Strategies
  ↓
Repository / ORM
  ↓
PostgreSQL
~~~

Each layer has a different responsibility.

## Controller / View

Responsible for transport concerns:

- request parsing
- authentication boundary
- request-level permission
- serializer validation
- invoking application use case
- mapping errors/results to HTTP

It should not calculate pricing or manually mutate domain state.

## Serializer

Serializer handles request shape/normalization:

~~~python
class ParkingEntrySerializer(serializers.Serializer):
    license_plate = serializers.CharField()
    vehicle_type = serializers.ChoiceField(
        choices=["bike", "car", "truck"]
    )
~~~

It should not become the whole business application.

## Application service

~~~python
class ParkVehicleService:
    def park_vehicle(self, license_plate, vehicle_type, gate_id):
        ...
~~~

The service does not return DRF Response. It returns application/domain result data.

## Result DTO

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class ParkingEntryResult:
    ticket_id: str
    spot_code: str
    entry_time: datetime
~~~

## API

~~~python
class ParkingEntryAPIView(APIView):

    def post(self, request):
        serializer = ParkingEntrySerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )

        result = parking_service.park_vehicle(
            **serializer.validated_data
        )

        output = ParkingEntryResultSerializer(
            result
        )

        return Response(
            output.data,
            status=201,
        )
~~~

## Business errors

Example:

~~~python
class ParkingFullError(Exception):
    pass
~~~

Map business errors to HTTP at the API boundary, ideally through centralized exception handling.

## Use-case endpoint vs arbitrary CRUD

Avoid allowing:

~~~text
PATCH /tickets/123
{"status": "closed"}
~~~

because that can bypass payment and spot-release workflow.

Prefer:

~~~text
POST /parking/exit
~~~

which represents the business use case.

## Read paths may differ

Read endpoints can use optimized selectors/query services rather than loading full aggregates.

## Transaction boundary

Application service/use-case handler is usually a natural place for transaction orchestration.

## Main lesson

Keep HTTP at the edge. Business workflow should remain callable from DRF, CLI, Celery, tests, or another interface.
