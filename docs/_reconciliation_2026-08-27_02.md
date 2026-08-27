# Reconciliation, 27 August 2026, second session of the day

Written **before** any work, under CLAUDE.md's session protocol. The first
session of the day left `docs/_reconciliation_2026-08-27.md`; this is the
second and it reconciles against the tree that session pushed. Each statement
names the command whose output establishes it. Nothing here is taken from the
previous reconciliation's word.

---

## 1. Branch, HEAD, push state

```
$ git rev-parse --abbrev-ref HEAD
fence-and-corpus-repairs

$ git status --porcelain
(empty)

$ git stash list
(empty)

$ git log --oneline origin/fence-and-corpus-repairs..HEAD
(empty)
```

**Clean tree, no stashes, nothing unpushed.** The failure the protocol exists
against, work committed and never pushed, did not recur: the previous session
ended by pushing and `origin` holds `c66f452`.

## 2. The last five commits

```
c66f452 Record the session protocol: reconcile at the start, push at the end
7574708 Run the report on the reconciled tree
fa9c9ad Name the budget re-stamp on rows 19, 20, 21a and 21b
ea713b1 Reconcile the tree against the register before repairing anything
6457b6c Register the intake budget; the decision is taken once and never re-raced
```

`fa9c9ad` is the one outstanding item the first reconciliation identified, and
it landed. Rows 19, 20, 21a and 21b each name `ce576a9fa04a7403` with
`intake_point_budget_s` as the causing field.

## 3. Tests

```
$ python -m pytest tests/ -q
218 passed in 2.21s
```

**218 passed, 0 failed**, matching the count in `CLAUDE.md`.

## 4. The registration verifies

```
$ python -c "... Registration.load('discovery_registration.json')"
hash        ce576a9fa04a7403 == registered_hash ce576a9fa04a7403
schema      cb1dffbfadbe3d58 == schema_fingerprint() cb1dffbfadbe3d58
verification verified
```

*The schema line is the state at the start of this session and item 1 moved it.
The fingerprint is now stored typed, `schema:cb1dffbfadbe3d58`; the digest, the
registration hash and the verification state are all unchanged.*

Both hash sets agree, and neither register carries a hash the other does not:

```
$ grep -o "[0-9a-f]\{16\}" docs/OPEN_ITEMS.md | sort -u
$ grep -o "[0-9a-f]\{16\}" docs/REGISTRATION_HISTORY.md | sort -u
701adbd9d48015ed  890a80e3a8566837  a06400ef28ebb54c  b8dd61e7eea6898e  ce576a9fa04a7403
```

## 5. Two findings the sweep turned up, both in `docs/OPEN_ITEMS.md`

Neither is in this session's instructed scope. Both are recorded here rather
than repaired, because a finding that exists only in a transcript did not
happen, and because changing a register row outside the instruction is the
operator's call and not this session's.

### Finding 1: line 68 names a superseded hash as the live one

```
$ grep -n "now hashes to" docs/OPEN_ITEMS.md
68: ... The registration in the tree now hashes to `701adbd9d48015ed`. *This
    line previously named `890a80e3a8566837`, which was the hash at the moment
    those rows closed and stopped being the current hash three re-stamps ago,
    so it contradicted rows 19 and 20 four lines above whilst reading as the
    live figure.*
```

The tree hashes to `ce576a9fa04a7403`. **The line is stale by exactly the
defect its own italicised sentence documents**, one re-stamp later: it names
`701adbd9d48015ed` as current whilst rows 19, 20, 21a and 21b nine lines above
name `ce576a9fa04a7403`. The italicised sentence should be read as a warning
that this line drifts on every re-stamp and not as a record that the drift was
fixed. **The repair is a correction to a record of a rule change and not to a
rule, so it is not a version and takes no §12.1 row**, on the same reasoning
the first reconciliation applied to rows 19 and 20.

### Finding 2: the closing paragraph names `archive_opens` as unset

Line 72 reads *"What now stands between the layer and a first sweep is the
archive's opening boundary ... Set `archive_opens` in the registration and the
US corpus becomes sweepable."* It is set:

```
archive_opens = 2023-01-01
```

and row 2 of `docs/REGISTRATION_HISTORY.md` names `archive_opens` as the field
that caused the stamp `a06400ef28ebb54c`, so it has been set since 26 August.
**The paragraph states as pending a thing the register elsewhere records as
done.** Whether a first sweep is now unblocked is a larger question than the
paragraph's staleness and is not answered here: the query fence, the want of a
client and the §14 freeze preconditions are separate blockers, and this finding
claims only that the reason the paragraph gives is no longer the reason.

## 6. What this session was instructed to do

Three items, one commit each: type the schema fingerprint so a hash sweep
cannot read it as a stamp; add a binding-path section to the run report; record
the scope question on §13 row 1 as a pending block. Row 21a stays **BLOCKED**
and row 21b stays **PROVISIONAL**, and neither is touched.
