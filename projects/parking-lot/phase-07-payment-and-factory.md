# Phase 07 — Payment + Factory Pattern

## Separate Payment from payment processing

Payment is domain state:

~~~text
payment_id
ticket_id
amount
method
status
provider reference
~~~

PaymentProcessor performs an operation.

Do not put provider/API workflow directly inside the Payment entity.

## Payment entity

~~~python
class PaymentStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment:
    def __init__(self, payment_id, ticket_id, amount, method):
        self.payment_id = payment_id
        self.ticket_id = ticket_id
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING

    def mark_success(self):
        self.status = PaymentStatus.SUCCESS

    def mark_failed(self):
        self.status = PaymentStatus.FAILED
~~~

## Processor contract

~~~python
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):

    @abstractmethod
    def process(self, payment):
        pass
~~~

Concrete processors:

~~~python
class CashProcessor(PaymentProcessor):
    def process(self, payment):
        ...


class CardProcessor(PaymentProcessor):
    def process(self, payment):
        ...


class UpiProcessor(PaymentProcessor):
    def process(self, payment):
        ...
~~~

## Factory

The caller has a PaymentMethod and needs the right processor.

~~~python
class PaymentProcessorFactory:

    @staticmethod
    def create(payment_method):
        if payment_method == "cash":
            return CashProcessor()

        if payment_method == "card":
            return CardProcessor()

        if payment_method == "upi":
            return UpiProcessor()

        raise ValueError("Unsupported payment method")
~~~

## PaymentService

~~~python
class PaymentService:

    def __init__(self, processor_factory):
        self.processor_factory = processor_factory

    def process(self, payment):
        processor = self.processor_factory.create(
            payment.method
        )

        try:
            processor.process(payment)
            payment.mark_success()
        except Exception:
            payment.mark_failed()
            raise
~~~

## Factory vs Strategy

Factory:

~~~text
Which concrete object should I create/select?
~~~

Strategy:

~~~text
Which algorithm should execute this behavior?
~~~

They often work together.

## Why a factory becomes more useful later

A realistic CardProcessor may require:

~~~python
CardProcessor(
    gateway=gateway,
    metrics=metrics,
    clock=clock,
)
~~~

Centralizing construction keeps clients from knowing constructor details.

## Do not create useless factories

If construction is simply:

~~~python
Payment()
~~~

a PaymentFactory adds little value.

## Payment failure rule

If payment fails:

~~~text
DO NOT
- release spot
- close ticket
- open exit gate
~~~

This business ordering becomes important in later transaction/recovery phases.
