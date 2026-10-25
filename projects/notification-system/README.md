# Notification System — Low-Level Design Learning Project

This project develops a notification system incrementally. The emphasis is not only on the final class diagram or code, but on the reasoning that turns an ambiguous product statement into an implementable design.

## Current scope

Phase 1 establishes what the system must do before classes, databases, queues, providers, or design patterns are selected.

- [Concept 1 — Requirement clarification](phase-01/01-requirement-clarification.md)
- [Concept 2 — Functional requirements and use cases](phase-01/02-functional-requirements.md)

## Confirmed Phase 1 decisions

| Question | Decision | Design consequence |
|---|---|---|
| One recipient or many? | Multiple recipients | One request may expand into several recipient deliveries. |
| Are templates required? | Yes | Callers may identify a reusable template and provide variable data. |
| Initial channels | Email, SMS, and push | The requirements remain channel-neutral while allowing channel-specific addresses. |
| Delivery result | Track per recipient and channel | A batch can be partially successful. |

These are learning-scope decisions, not claims that every production system must make the same choices.

## Progress tracker

| Phase | Concept | Status | Evidence |
|---|---|---:|---|
| 1 | 1. Clarify the problem and scope | Complete | [Notes, examples, diagrams, and exercises](phase-01/01-requirement-clarification.md) |
| 1 | 2. Derive functional requirements and use cases | Complete | [Requirements, flows, examples, and exercises](phase-01/02-functional-requirements.md) |
| 2+ | Object model, patterns, persistence, async delivery, reliability, and APIs | Not started | To be documented when each phase is completed |

## Phase 1 outcome

By the end of these two concepts, we can state the core contract in one sentence:

> Accept a notification request that names a template, supplies its data, selects one or more channels, and targets one or more recipients; validate it, render channel-appropriate content, attempt each recipient-channel delivery, and return or record the result of every attempt.

Phase 1 deliberately does **not** settle implementation choices such as Celery versus another worker, a particular database schema, or a vendor SDK. Those choices should follow the requirements instead of silently becoming requirements themselves.


