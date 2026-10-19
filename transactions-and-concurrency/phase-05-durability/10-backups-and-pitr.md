# 10. Backups and point-in-time recovery

## The problem: every live copy can contain the same mistake

At 14:00, an administrator accidentally deletes all orders.

Replication quickly copies that deletion to every replica. The replicas are doing their job; they are preserving the current state, including the mistake.

To recover the earlier state, you need history.

## Backups

A **backup** is a retained copy from which data can be restored.

Two broad forms:

| Type | What it captures | Typical consideration |
|---|---|---|
| Logical backup | Tables, rows, schema definitions, or logical objects | Restore cost and supported consistency scope |
| Physical backup | Database files and required recovery material | Engine-specific recovery and compatibility requirements |

A live database cannot generally be backed up safely by blindly copying arbitrary files at different moments. Use supported backup mechanisms or correctly coordinated snapshots.

## Base backup plus archived logs

A **base backup** supplies a starting database state.

**Archived logs** retain the required change history after or around that starting point, according to the engine's backup rules.

**Point-in-time recovery (PITR)** restores a base backup and replays logs until a chosen recovery target.

### Worked example

| Time | Event |
|---|---|
| 00:00 | Base backup taken |
| 09:00 | Orders created |
| 12:00 | Payments recorded |
| 14:00 | Accidental destructive transaction commits |

To recover before the mistake:
1. Provision an isolated recovery database.
2. Restore the appropriate base backup.
3. Supply the complete required archived-log sequence.
4. Replay to an engine-supported target before the destructive commit.
5. Verify the recovered data.
6. Decide how to return recovered information or service safely.

An exact transaction/log target can be more precise than an approximate wall-clock time. Target syntax and inclusion/exclusion behavior vary.

## Important limitation: stopping early excludes later good work too

Recovering the whole database to before 14:00 also excludes legitimate transactions after that target.

You may need an isolated restored instance to extract specific data or a reconciliation plan to preserve valid later changes. Do not assume full rollback in time selectively removes only the bad operation.

## RTO and RPO

**RTO**, Recovery Time Objective, is the acceptable restoration time.

**RPO**, Recovery Point Objective, is the acceptable data-loss window.

Examples:
- A recent backup with slow restore may meet RPO but fail RTO.
- A fast restore of an old backup may meet RTO but fail RPO.
- Frequent base backups without preserved recent logs may still lose recent work.

If logs are archived asynchronously, the most recent committed records might not yet exist in the archive when primary storage is lost.

## The chain must be complete

A missing required log segment can prevent recovery through that point. Base backups, log retention, archive success, and compatibility must be managed together.

“WAL exists on the primary” is different from “WAL is safely archived elsewhere.”

## Independent protection

Protect backups against the failures affecting live copies:
- Independent storage or failure domains.
- Appropriate access controls.
- Retention long enough to discover mistakes.
- Protection from unintended deletion or alteration.
- Monitoring of backup and archive failures.

## Restore testing

A successful backup job does not prove recoverability.

A meaningful restore test checks:
1. Backup can be retrieved.
2. Required keys and permissions are available.
3. Required logs exist.
4. Recovery completes.
5. Data and application checks pass.
6. Measured recovery time is acceptable.

## Final comparison

| Technique | Main contribution | Does not solve alone |
|---|---|---|
| WAL + flush | Crash recovery for committed data | Destruction of only storage |
| Checkpoints | Recovery progress and performance | Historical restore |
| Page protection | Incomplete-write recovery/detection | Every hardware disaster |
| Group commit | Efficient durable acknowledgement | Additional copies |
| Storage redundancy | Chosen component failures | Logical mistakes |
| Replication | Additional live copies | Historical mistakes copied everywhere |
| Backup + archived logs | Historical restore and disaster recovery | Instant availability or safe client retries |

## SDE1 takeaway

**A replica preserves another live copy. A backup preserves a recoverable historical copy. PITR combines a base backup with retained logs to recover to an appropriate point.**

You have now covered all ten durability techniques.
