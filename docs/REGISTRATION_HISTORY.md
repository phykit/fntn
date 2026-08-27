# Registration history: the chain of discovery-layer hashes

Every hash the discovery layer's registration has ever been stamped under, the
object each was taken over, and the field whose change caused the stamp.

**Why this file exists.** Rule 4 says nothing is deleted and nothing is
overwritten, and the registration was exempt from its own rule. `save` wrote
over whatever was already at the path, so each re-stamp destroyed the object
the previous hash was taken over, and a record carrying a superseded hash
pointed at a file that no longer existed in any form a reader could recover.
Two re-stamps had already happened when this file was written, and the object
behind the first of them survives only as a **reconstruction**: no commit
carries it. `Registration.save`
now refuses to overwrite a stamped registration unless the prior version's hash
and path are recorded here first.

**The hash is taken over the dataclass as well as the values, and this is the
part that surprises.** The 26 August object is one file, unchanged in the tree
from `1057c44` to `549836c`, and it hashes to `a06400ef28ebb54c` under the
schema of that span and to something else entirely under today's. Recomputing a
historical hash therefore needs the code of its own commit, not merely its own
bytes, and that is what the **object commit** column names and what
`test_registration_history_recomputes` checks out. A file recording only the
JSON would not be enough to reproduce a single row here.

Since the row for `701adbd9d48015ed`, the registration carries its own
`registered_hash`, so a file written from now on states the hash it was stamped
under and needs no reconstruction. It carries a **schema fingerprint** beside
it, a digest of the field names the hash is taken over, because a recorded hash
can only be checked whilst the dataclass is the one it was taken under.
`Registration.load` therefore reports one of three states: `unstamped`,
`verified`, or `unverifiable_schema_change`. **The third is not a failure and is
not a pass.** It is what a reader is owed when the file predates the current
shape: the recomputation would answer a different question, so no verification
is claimed. A file whose fingerprint matches and whose hash does not is refused
outright. Both provenance fields sit outside the hashed payload, so adding them
moved neither the hash nor the fingerprint.

**The provenance column** carries a §0.5 tag per row. `verified_primary` means
the object itself is retrievable at the commit named.
`reconstructed_hash_verified` means it is not: what is retrievable is a
reconstruction that reproduces the hash under the dataclass of the naming
commit, which is a positive verification and still not the artefact, so it
blocks the freeze signature exactly as `recollection` does.

## The chain

| # | Hash | Stamped (UTC) | Object commit | Registration object | Provenance (§0.5) | Field that caused this stamp |
|---|---|---|---|---|---|---|
| 1 | `890a80e3a8566837` | 2026-08-26T22:54:01.850224 | `3d3a09a` | `docs/registration_history/890a80e3a8566837.json`, a **reconstruction** of `discovery_registration.json` | `reconstructed_hash_verified` | n/a, the first stamp |
| 2 | `a06400ef28ebb54c` | 2026-08-26T22:54:01.850224 | `1057c44` | `git show 1057c44:discovery_registration.json` | `verified_primary` | `archive_opens` |
| 3 | `b8dd61e7eea6898e` | 2026-08-27T06:51:39.473454 | `e955d2b` | `git show e955d2b:discovery_registration.json` | `verified_primary` | `rulebook_stopwords` |
| 4 | `701adbd9d48015ed` | 2026-08-27T07:59:55.127137 | **current** | `discovery_registration.json` | `verified_primary` | `lexicon` |

Each cell in the object column is the command or path that yields the bytes,
and every one of them names `discovery_registration.json`, because that is what
`save` looks for: a row naming both the hash and the file it was the hash of.
The object commit is the commit whose `src/` defines the dataclass the hash was taken
over, which for rows 2 and 3 is also the commit that introduced those bytes.
The current row names no object commit because the commit carrying it does not
exist until it is made; **the row is completed with its SHA at the moment it is
superseded**, which is the moment `save` demands it be written down, and the
test fails a superseded row that has not been completed.

## Row 1 is a reconstruction, and what that is worth

`890a80e3a8566837` was recorded in `docs/OPEN_ITEMS.md` at commit `338381c` as
the hash under which §13 rows 19, 20 and 25 closed. **No commit carries the
file it was taken over.** The registration was untracked at the time and first
entered the tree at `1057c44`, by which point `archive_opens` had been added
and set, so the object that hashed to `890a80e3a8566837` was overwritten before
it was ever committed. That is the defect this file exists against, observed in
its own history.

The object in `docs/registration_history/` is the 26 August registration as
committed at `1057c44` with `archive_opens` removed, which is the only field
that separates the two. **Its whole credential is that it reproduces the hash**
under the dataclass of `3d3a09a`, the commit before `archive_opens` was added,
and that is a real credential rather than a circular one: it was derived from
the known successor by removing one field, not searched for. It is recorded as
a reconstruction all the same, because a document that reproduces a hash and a
document that is the original are two different claims and only the weaker one
is true here.

*The honest limit.* The hash is SHA-256 truncated to sixteen hex characters, so
sixty-four bits. A deliberate search could find a second preimage; nothing here
searched for one.

## Row 2's object is recovered; its attribution is inferred

Row 2's bytes are in git and recompute exactly, so the object is recovered and
the row is not a reconstruction. What is inferred is the *attribution*: the 26 August
object was stamped once, at 22:54:01, and acquired two hashes without being
re-stamped, because `archive_opens` was added to the dataclass at `338381c`
whilst the file sat untracked. Rows 1 and 2 therefore share a `registered_at`.
That is not a fault in the timestamp: `stamp` refuses to move one, correctly.
It is the same defect from the other side, a hash moving whilst the commitment
and its timestamp stand, and §13 rows 19 and 20 say so in those words.

## What a row does not mean

A new hash is a new object, never on its own a new commitment. Rows 19 and 20
of `docs/OPEN_ITEMS.md` carry δ, *n*ₘᵢₙ, the ratio and the seed, and those four
values are identical in every row above: they were committed blind on 26 August
2026, before any archive exists, and no re-stamp since has touched them. A
re-stamp caused by `archive_opens`, `rulebook_stopwords` or `lexicon` is a new
hash on an unmoved commitment. A re-stamp caused by δ would be a new
commitment, and the distinction is the reason the causing field is a column
here rather than a note.
