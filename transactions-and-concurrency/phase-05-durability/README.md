# Phase 05 — Durability techniques

**Durability means confirmed commits survive the failures covered by the system's guarantee.** It requires a clearly defined acknowledgement policy and trustworthy storage. It is not a promise that no imaginable disaster can lose data.

Read these ten lessons in order:

| # | Lesson | Main problem |
|---|---|---|
| 1 | [Write-ahead logging](01-write-ahead-logging.md) | Recover committed changes without writing every data page at commit |
| 2 | [Flushing to persistent storage](02-flushing-and-fsync.md) | A write reaching RAM is not necessarily durable |
| 3 | [Crash recovery: redo and undo](03-crash-recovery-redo-undo.md) | Reconstruct a valid state after interruption |
| 4 | [Checkpoints](04-checkpoints.md) | Bound recovery work and support log lifecycle management |
| 5 | [Incomplete page writes](05-torn-page-protection.md) | A page can be partly old and partly new after a crash |
| 6 | [Group commit](06-group-commit.md) | Avoid one expensive flush per transaction |
| 7 | [Reliable storage and redundancy](07-storage-and-redundancy.md) | Survive hardware faults within the chosen design |
| 8 | [Synchronous replication](08-synchronous-replication.md) | Preserve acknowledged data on another server |
| 9 | [Asynchronous replication](09-asynchronous-replication.md) | Maintain copies without waiting, accepting a loss window |
| 10 | [Backups and point-in-time recovery](10-backups-and-pitr.md) | Recover from destructive mistakes or larger failures |

## How they work together

A typical logging-based database generates recovery records, flushes required records before acknowledging a durable commit, writes data pages over time, and uses logs after a crash. Checkpoints limit recovery work. Page protection handles incomplete writes. Group commit shares flush cost.

Storage redundancy and replication cover additional hardware/server failures. Backups and archived logs allow restoration after failures that live copies cannot solve.

Not every database uses identical algorithms. Redo/undo design, checkpoint semantics, page protection, and replication acknowledgement modes are engine-specific. These lessons explain concepts rather than universal internal procedures.

## Important distinctions

| Term | Meaning |
|---|---|
| Local durability | Commit survives covered failures of the database process/machine while required storage survives |
| Replication durability | Required copies of committed data exist under a specified acknowledgement policy |
| Availability | Service can continue accepting or serving work |
| Backup recoverability | An independent historical copy can be restored |
| RPO | Recovery Point Objective: acceptable amount of data loss measured as a time window |
| RTO | Recovery Time Objective: acceptable time to restore service |

Replication can improve availability and durability, but a replica is not automatically a backup. A healthy-looking backup is not proven recoverable until restoration is tested.

## Failure thought experiment

For each technique ask:
1. What is persisted?
2. At what point can the application receive success?
3. What happens if power fails immediately afterward?
4. What if the disk is destroyed?
5. What if an accidental DELETE is replicated everywhere?
6. Can the client determine whether its transaction committed if the response is lost?

The final question still requires operation identifiers and idempotency; storage durability alone cannot resolve the client's uncertainty.
