# 8. Synchronous replication

## The problem: one server's storage can disappear

Local durable logging can survive a process crash if its storage survives. It cannot preserve the only copy when the entire storage is destroyed.

**Replication** maintains database data on additional servers. A **primary** accepts writes; a **replica** receives changes in a common primary/replica design.

**Synchronous replication makes commit acknowledgement wait for a required replication condition.**

That condition must be specified precisely.

## The acknowledgement stages are different

A replica might acknowledge that it:
1. Received log bytes in memory.
2. Wrote bytes to its operating-system buffers.
3. Flushed bytes to durable storage.
4. Applied changes so they are available to queries.

Receiving, persisting, and applying are not interchangeable.

For a guarantee against loss of the primary and volatile memory, a memory-only receipt is insufficient.

## Example: remote durable acknowledgement

1. A transfer executes on the primary.
2. Required local commit records become durable.
3. The replica receives the required log.
4. The replica durably flushes it.
5. The primary receives acknowledgement.
6. The client receives success.

If the primary is then destroyed, the required replica has the persisted records.

This example assumes an appropriate local-plus-remote durability policy. Actual database modes may use different conditions.

## Persisted does not always mean immediately readable

A replica can have a durable log record that it has not yet replayed into query-visible state.

After promotion or recovery, it can apply that record. If your requirement is immediate replica query visibility, that needs an applied/replayed acknowledgement policy or another read consistency mechanism.

## Failure and latency trade-offs

If the required replica is unavailable, the primary may need to wait or reject commits.

If operators or automatic policy downgrade to asynchronous acknowledgement, availability may improve while the durability guarantee changes.

Network round trips and remote flush latency can increase commit latency. Greater geographic distance can increase that cost.

## Required replicas and quorum

A **quorum** is a required number or set of participants whose acknowledgements satisfy a policy.

A system might wait for one eligible replica or several. Surviving a failure depends on which nodes acknowledged, which nodes survive, and which node is promoted.

Replication configuration alone does not prove that arbitrary failover to any replica is lossless. Promotion must select a sufficiently up-to-date node and avoid unsafe competing primaries.

## What synchronous replication does not solve

- Accidental deletes can be replicated faithfully.
- Lost client commit responses remain uncertain to the client.
- An external payment does not automatically join the database transaction.
- Failure of every required copy can still lose data.

## SDE1 takeaway

“Synchronous” is incomplete without answering: **synchronous up to receipt, durable flush, or application—and on how many nodes?**

Next: [Asynchronous replication](09-asynchronous-replication.md).
