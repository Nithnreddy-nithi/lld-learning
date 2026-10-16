# Phase 18 — Adapter Pattern & External Integrations

## Problem

Our application wants one clean payment contract.

But providers expose incompatible APIs.

Razorpay may conceptually expose:

~~~text
capture(payment_id, amount)
status = "captured"
~~~

Stripe may expose:

~~~text
create_payment_intent(...)
status = "succeeded"
~~~

PaymentService should not contain provider-specific branches.

## Target interface

This is what *our application* wants.

~~~python
from abc import ABC, abstractmethod

class PaymentGateway(ABC):

    @abstractmethod
    def charge(self, payment_id, amount):
        pass
~~~

## Normalized result

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class PaymentGatewayResult:
    success: bool
    provider_reference: str | None
    failure_code: str | None = None
~~~

A richer production version may use:

~~~text
SUCCESS
FAILURE
UNKNOWN
~~~

because timeout is not necessarily failure.

## Razorpay Adapter

~~~python
class RazorpayPaymentGateway(PaymentGateway):

    def __init__(self, razorpay_client):
        self.razorpay_client = razorpay_client

    def charge(self, payment_id, amount):

        response = self.razorpay_client.capture(
            payment_id,
            amount.minor_units,
        )

        if response["status"] == "captured":
            return PaymentGatewayResult(
                success=True,
                provider_reference=response["id"],
            )

        return PaymentGatewayResult(
            success=False,
            provider_reference=response.get("id"),
            failure_code=response.get("error_code"),
        )
~~~

## Stripe Adapter

~~~python
class StripePaymentGateway(PaymentGateway):

    def __init__(self, stripe_client):
        self.stripe_client = stripe_client

    def charge(self, payment_id, amount):

        response = self.stripe_client.create_payment_intent(
            reference=payment_id,
            amount=amount.minor_units,
            currency=amount.currency,
        )

        return PaymentGatewayResult(
            success=(
                response["status"]
                == "succeeded"
            ),
            provider_reference=response["id"],
        )
~~~

## PaymentService

~~~python
class PaymentService:

    def __init__(self, payment_gateway):
        self.payment_gateway = payment_gateway

    def process_payment(self, payment_id, amount):
        return self.payment_gateway.charge(
            payment_id,
            amount,
        )
~~~

PaymentService knows no Razorpay/Stripe status names.

## Roles

~~~text
PaymentService              = Client
PaymentGateway              = Target
RazorpayPaymentGateway      = Adapter
Razorpay SDK                = Adaptee
PaymentGatewayResult        = normalized application result
~~~

## Exception translation

Provider-specific exceptions should not leak deeply into application code.

Adapter can convert:

~~~text
RazorpayTimeoutError
->
PaymentGatewayTimeout
~~~

Timeout may map to UNKNOWN outcome rather than FAILED.

## Anti-Corruption Layer

The adapter prevents provider concepts from contaminating the domain:

- provider status strings
- SDK objects
- payload structure
- amount units
- provider error types

## Adapter beyond payments

Same idea for:

- SMS provider
- email provider
- license-plate scanner
- physical gate controller
- cloud storage
- external maps

## Webhook adapter

Webhook layer verifies provider signature and converts provider payload to internal application event/command.

## Adapter vs Factory

Factory chooses/creates the implementation.

Adapter translates interface.

## Adapter vs Strategy

Strategy = interchangeable algorithm.

Adapter = compatibility translation.

## Adapter vs Facade

Facade = simplified interface to a complex subsystem.

Adapter = make incompatible interface match what client expects.

## ISP note

If a provider supports charge/refund/status but a client only needs charge, consider small capability ports:

~~~python
class ChargeGateway(Protocol):
    def charge(...): ...

class RefundGateway(Protocol):
    def refund(...): ...
~~~

## Hexagonal architecture connection

Ports are application-owned interfaces:

~~~text
PaymentGateway
TicketRepository
EventPublisher
~~~

Adapters implement them:

~~~text
Razorpay
Django ORM
Kafka
~~~

DRF itself can be considered an inbound adapter.

## Main lesson

The application defines the interface it needs. Provider-specific adapters translate the outside world into that interface.
