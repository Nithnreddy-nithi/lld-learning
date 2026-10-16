# Phase 01 — Requirements & Use Cases

## Goal
Understand the problem before creating classes.

## Initial scope
- One parking lot, multiple floors and spots.
- Vehicle types: BIKE, CAR, TRUCK.
- Spot types: BIKE, COMPACT, LARGE.
- Entry: find compatible spot → assign → create ticket.
- Exit: calculate fee → payment → release spot → close ticket.
- Multiple entry/exit gates.
- Parking full raises an error.

## Pricing
- Bike: ₹20/hour
- Car: ₹40/hour
- Truck: ₹60/hour
- Partial hour rounds up.

## Main use cases
Park vehicle, find spot, generate ticket, calculate fee, process payment, exit vehicle, release spot.

## Reusable design questions
What must the system do? Who interacts with it? What are the workflows? What objects exist? What responsibilities belong to each object? What is likely to change?

Start from behavior and workflows, not classes.
