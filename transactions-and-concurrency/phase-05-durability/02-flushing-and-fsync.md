# 2. Flushing to persistent storage

## The problem: “written” can mean different things

The database writes a commit log record. Is it safe to tell the client success?

Not necessarily. The bytes may still exist only in a temporary buffer.

A **buffer** is memory used to hold data temporarily before another layer processes it.

A simplified write path is:

1. Database log buffer in RAM.
2. Operating-system cache in RAM.
3. Device or controller cache.
4. Durable storage media, or appropriately protected non-volatile storage.

The exact path differs between operating systems and hardware.

## What a normal write can do

A normal file write can copy data into the operating system's cache and return before the storage has durably persisted it.

Example:

| Time | Event |
|---|---|
| 1 | Database writes commit record to OS cache |
| 2 | Application receives success too early |
| 3 | Machine loses power |
| 4 | Cached record disappears |

If no other durable copy exists, the acknowledged transaction can be lost.

## What flushing means

A **flush** asks the relevant layer to push buffered writes toward durable storage and wait for the required guarantee.

Databases use operating-system facilities such as fsync or equivalent mechanisms.

Conceptually:

~~~text
Generate log records
Write records
Request durable synchronization
Wait for successful completion
Acknowledge commit
~~~

A flush is not just “emptying a variable.” It is coordination across the storage stack.

## Database crash versus power failure

| Failure | What might survive? |
|---|---|
| Database process alone crashes | OS-cached data can remain |
| Whole machine loses power | Ordinary volatile OS caches disappear |
| Storage device is destroyed | Data on that device can be lost |

A setting that appears safe in process-crash tests can still lose data after power failure.

## Why hardware behavior matters

The database trusts the operating system and storage device's durability acknowledgements. A device that incorrectly reports persistence can break the assumption.

Protected write caches can be durable if they have suitable power-loss protection. An unprotected volatile device cache is different.

## Configuration trade-off

An engine may offer settings that acknowledge before a durable flush. This can reduce latency, but recent acknowledged transactions may be lost after a crash.

Understand what a setting changes: local flushing, remote replication acknowledgement, or both. Do not treat every option containing “sync” as the same guarantee.

## Relation to WAL

WAL says what must be recorded and the required ordering. Flushing makes the necessary records durable. A log file name on disk is not proof its latest contents are persisted.

## SDE1 takeaway

Before saying “commit is saved,” ask: **saved in which layer, and did success wait for durable persistence?**

Next: [Crash recovery](03-crash-recovery-redo-undo.md).
