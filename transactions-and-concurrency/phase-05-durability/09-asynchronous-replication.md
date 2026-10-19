# 9. Asynchronous replication

## The problem: waiting for remote servers has a cost

A system may want remote copies without making each commit wait for a network round trip and remote storage.

**Asynchronous replication allows the primary to acknowledge commits without waiting for the replica to reach the corresponding replication point.**

The primary can still make each commit locally durable.

## Example timeline

| Time | Primary | Replica |
|---|---|---|
| 1 | Durably commits transaction 100 | Has through 100 |
| 2 | Durably commits 101; acknowledges client | Still at 100 |
| 3 | Durably commits 102; acknowledges client | Still at 100 |
| 4 | Primary storage is destroyed | Still at 100 |

If the replica is promoted and no other recovery source survives, transactions 101 and 102 are missing from the new primary, even though clients received success.

They were locally durable but were not protected against the loss of that local storage.

## Replication lag

**Replication lag** is how far a replica is behind the primary, measured by time, bytes, or log position.

Lag can grow because of:
- Network delays.
- Slow replica storage.
- Heavy replay work.
- Long outages.
- Workload spikes.

Receiving lag and apply lag are distinct: a replica may possess log bytes but not yet expose their effects to queries.

## Read-after-write issue

A client creates an order successfully on the primary, then immediately reads from a lagging replica.

The replica may return “order not found.”

That does not necessarily mean the primary lost the order. The replica may simply not have applied it yet.

Applications may route immediate reads to the primary, wait for a known replication position, or use another consistency mechanism depending on requirements.

## RPO

**Recovery Point Objective (RPO)** is the acceptable data-loss window after failure.

If business policy says “lose at most five seconds of transactions,” the architecture and operations must support that target.

An observed two-second lag is not a hard promise that loss can never exceed two seconds. Outages can increase lag. Monitor it and define what happens when targets are exceeded.

## Benefits and trade-offs

| Benefit | Trade-off |
|---|---|
| No remote acknowledgement on the commit path | Replica may lack acknowledged transactions |
| Remote temporary failure need not block local commits | Growing lag and retained log requirements |
| Additional read or recovery copies | Reads may be stale |
| Geographic copies | Failover correctness and RPO need explicit design |

## Compare synchronous replication

Synchronous replication waits for a chosen remote condition. Asynchronous replication does not wait for that condition before acknowledging.

Neither is a substitute for historical backups, and both need correct failover procedures.

## SDE1 takeaway

**Asynchronous replication improves copy availability without automatically guaranteeing zero loss of acknowledged writes after primary storage loss.**

Next: [Backups and point-in-time recovery](10-backups-and-pitr.md).
