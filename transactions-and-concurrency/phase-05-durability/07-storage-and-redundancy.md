# 7. Reliable storage and redundancy

## The problem: durable data can still live on failed hardware

A transaction can be correctly flushed to an SSD. If that SSD is later destroyed and it holds the only copy, the data can still be lost.

Durability must be considered against an explicit failure model.

A **failure model** describes the failures the design intends to survive: process crash, power loss, one disk failure, server loss, or site loss.

## Reliable persistence

The storage stack must correctly implement the database's requirements:
- Required writes reach durable media or protected non-volatile caches.
- Flush and ordering requests are honored.
- Write errors are reported.
- The filesystem and hardware do not falsely acknowledge persistence.

Power-loss protection can make certain device caches safe. An ordinary volatile cache is different.

An uninterruptible power supply can reduce power interruptions, but it does not replace correct persistence, redundancy, or backups.

## Redundancy

**Redundancy** means maintaining additional copies or information so some component failures do not destroy the data.

Example: mirrored storage writes the same data to two devices.

| Failure | Possible outcome with a healthy mirror |
|---|---|
| One device fails | Other device can retain data |
| Application deletes records | Deletion affects the live logical data on both |
| Both devices fail together | Data may be lost |
| Entire server or site is destroyed | Local mirror may be lost |

The mirror protects against specific hardware failures, not every form of data loss.

## RAID basics

**RAID** is a family of ways to combine disks for redundancy and/or performance.

For SDE1, understand that some layouts mirror data, some use parity, and some provide no redundancy. You do not need to memorize every layout's implementation before learning transaction correctness.

Rebuilding a failed array takes time and creates an operational risk period.

## Independent copies matter

Two files on one disk are not protection against that disk's destruction.

Two disks in one server are not protection against every server failure.

Two servers in one site are not protection against destruction of that site.

The required copy locations depend on the failures you must survive.

## Storage redundancy is not a backup

Redundancy typically mirrors current state. It can faithfully preserve an accidental destructive write.

A backup preserves a recoverable historical state under a retention policy. Keep restoration capability independently from the live system where appropriate.

## SDE1 takeaway

Ask two questions:
1. Did the commit reach trustworthy durable storage?
2. Which component failures can remove every surviving copy?

Next: [Synchronous replication](08-synchronous-replication.md).
