# 5. Protection against incomplete page writes

## The problem: a page is not always an indivisible device write

Suppose the database page is 8 KB, but the storage stack can write it in smaller pieces.

A crash can occur after the first part is written and before the rest.

The resulting page may contain:
- First part from the new version.
- Remaining part from the old version.

This is a **torn page** or **partial-page write**.

It is not merely an old but valid page. Its internal structure may be inconsistent.

## Why ordinary change records may be insufficient

Suppose a log record says “modify the balance field at this location.”

That can be replayed safely only if recovery has an appropriate valid page structure or enough information to reconstruct it.

If the page header or layout is torn, a small field-level record may not be sufficient.

Databases use different protection techniques.

## Technique A: full-page images

A **full-page image** stores a complete page image in the recovery log at appropriate times.

If a page is torn, recovery can use a logged complete image as a valid basis and replay later changes.

It need not log a full page for every tiny update. Engines can use rules such as logging an image on the first relevant modification after a checkpoint.

Trade-off: increased log volume and storage traffic.

## Technique B: doublewrite

A **doublewrite buffer** is an intermediate area where a recoverable copy of a page is written before its final location is overwritten.

Conceptually:
1. Write the page copy to the protected intermediate area.
2. Ensure that copy is persisted.
3. Write the page to its final data-file location.
4. If that final write tears, recover using the intermediate copy.

This increases writing, but provides a source for restoring an intact page. Implementations batch and optimize the process.

## Technique C: checksums

A **checksum** is a calculated value used to detect unexpected changes to stored bytes.

On reading a page, the database compares the calculated checksum with the stored checksum. A mismatch indicates possible corruption.

Important: **detection is not repair**. A checksum can reveal damage without providing the missing correct bytes. Repair needs another source: log image, doublewrite copy, replica, or backup, depending on the design.

## Other approaches

Copy-on-write designs can write a new page elsewhere and carefully switch references rather than overwriting a live page in place. This is an alternative design family, not a setting every database offers.

Storage atomic-write guarantees can also help when the page size, alignment, and device guarantees match the database's requirements.

## Why backend developers should know this

The statement “the commit log is durable” is only part of recovery correctness. The engine and storage must also handle damaged pages appropriately.

Do not disable page-write protection for a small benchmark gain without understanding the engine's requirements and failure consequences.

Next: [Group commit](06-group-commit.md).
