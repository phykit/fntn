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

**The fingerprint is written `schema:<digest>` and is not a hash.** It was
stored as sixteen bare hex characters, which is exactly the shape of a
registration hash, so a sweep of `discovery_registration.json` for unrecorded
stamps found two values and could only be told by a person that one of them was
not a stamp. The reconciliation of 27 August had to write a paragraph saying so.
A check that a person has to complete is not machine-checkable, and by this
project's own standard that makes it not a check. The prefix types the value so
that no sweep for a hash can read it as one. It is not part of the digest and
reaches neither hash, so typing it moved nothing: `ce576a9fa04a7403` is the
hash before and after, and no row was added above. `Registration.schema_matches`
accepts the superseded bare encoding as naming the same shape, because a bare
digest equal to today's digest establishes exactly what the fingerprint is
asked to establish, and reporting `unverifiable_schema_change` over it would be
*cannot verify* said of something that can be verified.

## The sweep

Registration hashes are found in a file with this and nothing looser:

```
(?<![:0-9a-fA-F])[0-9a-f]{16}(?![0-9a-fA-F])
```

The colon in the lookbehind is what excludes the digest half of a typed
fingerprint; **the trailing guard is what stops a longer hex run yielding a
false sixteen.** *The cost, stated:* a naked `[0-9a-f]{16}` ignores token
boundaries and matches inside `schema:cb1dffbfadbe3d58` regardless, so the
prefix types the record and does not on its own repair a careless sweep. That is
why the pattern is written here, beside the chain it is swept against, and why
`test_a_hash_sweep_of_the_registration_finds_only_registration_hashes` runs it
against the real file and asserts this document still states it verbatim. Every
token it yields must appear in the chain below.

**One file in the tree still carries the untyped encoding: none.** `save`
writes the typed form unconditionally, and `discovery_registration.json` was
re-saved when the prefix landed. Any registration written elsewhere keeps the
bare encoding until it is next stamped, which is a real limit and is why the
loader still accepts it.

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
| 4 | `701adbd9d48015ed` | 2026-08-27T07:59:55.127137 | `d84fd5b` | `git show d84fd5b:discovery_registration.json` | `verified_primary` | `lexicon` |
| 5 | `ce576a9fa04a7403` | 2026-08-27T09:06:19.906138 | `cac46f6` | `git show cac46f6:discovery_registration.json` | `verified_primary` | `intake_point_budget_s` |
| 6 | `d47d1fe876dafe36` | 2026-08-27T09:06:19.906138 | `2b571c0` | `git show 2b571c0:discovery_registration.json` | `verified_primary` | `max_tolerable_fixed_cost_bps` |
| 7 | `61fafd4ac5c6e99b` | 2026-08-27T09:06:19.906138 | `9fe7e9f` | `git show 9fe7e9f:discovery_registration.json` | `verified_primary` | `audit_fraction` |
| 8 | `fcfa57a15a011b33` | 2026-08-27T09:06:19.906138 | `e965230` | `git show e965230:discovery_registration.json` | `verified_primary` | `theta` |
| 9 | `eb3bbe92c34d1e6f` | 2026-08-27T09:06:19.906138 | `0cabf9b` | `git show 0cabf9b:discovery_registration.json` | `verified_primary` | `delta_min_floor` |
| 10 | `09e1e23c447edf92` | 2026-08-27T09:06:19.906138 | `bb49304` | `git show bb49304:discovery_registration.json` | `verified_primary` | `discoverable_classes` |
| 11 | `81e9b57128f9285a` | 2026-08-27T09:06:19.906138 | `bd1a345` | `git show bd1a345:discovery_registration.json` | `verified_primary` | `corpora` |
| 12 | `2616ba37fb307c0e` | 2026-08-27T09:06:19.906138 | `df5f721` | `git show df5f721:discovery_registration.json` | `verified_primary` | `max_tolerable_fixed_cost_bps` |
| 13 | `827cf0d8c84791e8` | 2026-08-27T09:06:19.906138 | `270066e` | `git show 270066e:discovery_registration.json` | `verified_primary` | `delta_min_floor` |
| 14 | `bbfc50c781de67b5` | 2026-08-27T09:06:19.906138 | `db1c463` | `git show db1c463:discovery_registration.json` | `verified_primary` | `agent_model` |
| 15 | `79280b2b50e8fd0b` | 2026-08-27T09:06:19.906138 | `0d3997f` | `git show 0d3997f:discovery_registration.json` | `verified_primary` | `discoverable_classes` |
| 16 | `4ee72126ce99fd79` | 2026-08-27T09:06:19.906138 | `271549f` | `git show 271549f:discovery_registration.json` | `verified_primary` | `agent_prompt_sha` |
| 17 | `6ed075bc9378be04` | 2026-08-27T09:06:19.906138 | `30087bf` | `git show 30087bf:discovery_registration.json` | `verified_primary` | `proposal_schema_sha` |
| 18 | `a109a854b7083776` | 2026-08-27T09:06:19.906138 | **current** | `discovery_registration.json` | `verified_primary` | `structured_outputs_strict` |

Each cell in the object column is the command or path that yields the bytes,
and every one of them names `discovery_registration.json`, because that is what
`save` looks for: a row naming both the hash and the file it was the hash of.
The object commit is the commit whose `src/` defines the dataclass the hash was taken
over, which for rows 2 and 3 is also the commit that introduced those bytes.
The current row names no object commit because the commit carrying it does not
exist until it is made; **the row is completed with its SHA at the moment it is
superseded**, which is the moment `save` demands it be written down, and the
test fails a superseded row that has not been completed.

## Rows 12 and 13 re-derive two values, and one of them was written twice

*Row 12's causing field is `max_tolerable_fixed_cost_bps`, **§13 row 29**,
re-derived from 10.0 bp to **8.7 bp** on 27 August 2026 (`§12.1` P134) once
§0.12 stated reference equity. Row 13's is `delta_min_floor`, **§14's floor**,
which follows by the arithmetic `7.0 + 8.7` from 17.0 bp to **15.7 bp**.*

**Two stamps and not one, deliberately.** Each names the single field that
caused it, as rows 5 to 10 do. *A stamp naming two fields records that
something changed and leaves a reader to work out which change mattered, and
the causing-field column exists precisely so that they do not have to.*

***AND THE SESSION THAT WROTE THEM BROKE THE RULE ONCE, WHICH IS RECORDED
BECAUSE THE CHAIN CAUGHT IT.*** Both saves were first made in one working
tree with **no commit between them**, so row 12 named a hash whose object
existed in **no commit at all** and row 12's own object column would have said
`current` for a file that had already moved on.
`test_a_superseded_row_carries_its_object_commit` and
`test_registration_history_recomputes` both failed, naming row 12 exactly.
**The sequence was redone as one save, one commit**, which is what row 12's
`df5f721` now records. *The rule was already written; what was missing was an
occasion to find out that it binds. The guard also refused the rollback,
because rolling back would itself have destroyed a stamped object.*

**`registered_at` has still not moved**, and rows 12 and 13 share
`2026-08-27T09:06:19.906138` with rows 5 to 11. ***That is not a defect and it
is the second time it needs saying.*** The timestamp records when the
commitment was made, and the commitment recorded at that instant — the control
arm's δ and *n*ₘᵢₙ, its ratio and its seed — **has not moved and cannot be
moved by a cost tolerance.** *A timestamp that moved whenever any field did
would record the last edit, which is what `git log` is for.*

## Row 6 shares row 5's timestamp, and that is the mechanism working

*Row 6's causing field is `max_tolerable_fixed_cost_bps`, which is **§13 row 29**, the maximum tolerable fixed cost, set to **10 bp** on 27 August 2026 on delegated authority. The attribution is written here and not in the table's last column, because `test_every_causing_field_names_a_real_field_or_the_first_stamp` reads that column mechanically and a cell carrying a field name plus a gloss is a cell that no longer names a field.*

`registered_at` did not move when row 29 entered the object, because `stamp`
refuses to move a timestamp whose whole purpose is that it cannot move. **Rows 5
and 6 therefore carry the same `2026-08-27T09:06:19.906138`**, exactly as rows 1
and 2 do, and for the same reason: **a hash moved whilst the commitment and its
timestamp stood.**

*That is the distinction this file exists to keep.* A new hash is a new
**object**. It is a new **commitment** only where the field that caused it is
one of δ, *n*ₘᵢₙ, the ratio or the seed, and row 6's causing field is none of
those. §13 rows 19 and 20 say so in those words and are unmoved by this row.

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

## Row 14 registers a value that was never registered, which is why it is here

*Row 14's causing field is `agent_model`, **§13 row 39**, set to
`claude-sonnet-5` on 27 August 2026.*

**The field did not exist until this stamp, and row 39 said it did.** Row 39
was written on 27 August 2026 asserting that *the pinned identifier is a
registered field and re-pinning re-stamps*. It was not one. The pin lived as a
default string in `src/fntn/scanner/clients.py` and a second copy as an
argparse default in `src/fntn/scanner/cli.py`, and **a change to either would
have moved what every future sweep produced whilst moving no hash and leaving
no row here.** The correction is `docs/CORRECTIONS.md` B15.

***So this row records two different things at once and the difference
matters.*** The **schema** moved: the field is new, the fingerprint moved from
`schema:cb1dffbfadbe3d58` to `schema:a392b1fd72119c24`, and every registration
written before it now reports `unverifiable_schema_change` rather than
`verified`, which is the third state doing its job. The **value** did not move
in the sense of a commitment being revised: it was `claude-opus-4-6` in the
code and is `claude-sonnet-5` in the registration, and *nothing was ever swept
under the old one*, so no result is made non-comparable by the change.

**What the operator is buying with this row, stated as a cost.** Every future
re-pin is now a re-stamp: a new hash, a row here, and rows 19, 20, 21a and 21b
re-read to confirm the commitment behind each has not moved. *That is the
expense, and it is the point:* a pin that can move cheaply moves, and two
sweeps under two pins are not comparable however similar the models are.

**Rows 19, 20, 21a and 21b do not move under this stamp.** δ, *n*ₘᵢₙ, the ratio
and the seed are byte-identical to their 26 August values in every row of the
chain above, and the causing field of this stamp reaches none of them: which
model reads a corpus cannot change how far apart the arms must be before the
difference counts, and it cannot redraw a seed. The 21a reading of 0 of 36 and
21b's five closed routes were taken under `701adbd9d48015ed` against
`docs/labelled_proposals.json` with clerk labels already written, and this
stamp changes no rule the fence applies, so **neither reading is restated under
`bbfc50c781de67b5`** and neither is carried forward.
