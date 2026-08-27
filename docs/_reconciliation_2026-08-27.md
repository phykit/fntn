# Reconciliation, 27 August 2026

Written **before** any repair work, so that a second disconnect leaves the
diagnosis on disk rather than in a transcript. A previous session was given a
three-commit instruction (row 21 split, run report, intake budget) and was
disconnected at an unknown point. Nothing below is assumed; each statement
names the command whose output establishes it.

---

## 1. Branch, HEAD, push state

```
$ git rev-parse --abbrev-ref HEAD
fence-and-corpus-repairs

$ git rev-parse HEAD
6457b6c29b6bb6ac9616cbea73eb1ba694caa09c

$ git stash list
(empty)

$ git status --short
(empty)

$ git push origin HEAD
   e955d2b..6457b6c  HEAD -> fence-and-corpus-repairs
```

**The working tree was clean and there were no stashes**, so Phase 0a's
preservation branch was not needed and none was made. There was nothing to
preserve, which is a fact about this tree and not a claim that the previous
session left nothing behind: it committed everything it wrote.

**The branch was three commits ahead of `origin` when this session began.**
`e955d2b..6457b6c` is the range that had been committed and never pushed, which
is precisely the three commits of the instruction. They were pushed before any
further work, because losing them twice is the failure mode.

## 2. The last eight commits

```
$ git log --oneline -8
6457b6c Register the intake budget; the decision is taken once and never re-raced
d84fd5b Add the run report: eight sections, and a queue that refuses to rank
3b6102c Split §13 row 21 into 21a and 21b, and add the ratification harness
3293402 Keep the raw pages, make the provenance vocabulary total, verify the stored hash
99aefa1 Store the discovery corpus as extracted text; the corpus residue falls to nil (row 22)
7fd2315 Record every registration hash, and put the lexicon in the object it is hashed with
e955d2b Narrow the designator branch; register the fence's stopword set (row 21)
549836c Strip LII page chrome at fetch time; record both byte counts (row 22)
```

The top three are the three commits of the instruction, in the instructed
order. **The subject lines are not evidence that the work landed**, and each is
checked against the tree below rather than taken at its word.

## 3. Tests

```
$ python -m pytest tests/ -q
218 passed in 2.45s
```

**218 passed, 0 failed.** The figure matches the count in `CLAUDE.md`, which is
worth stating because it initially reads as evidence that no new tests landed.
It is not: `CLAUDE.md` was updated to 218 by the same run of commits, and the
named tests of commits 2 and 3 are present and are listed below. The count
agreeing with the register is the register having been maintained, which is the
condition this reconciliation exists to check.

## 4. COMMIT 1, the row 21 split: **LANDED, complete**

| Required | Found | Evidence |
|---|---|---|
| 21a and 21b as separate rows | yes | `docs/OPEN_ITEMS.md` lines 59 and 60, two rows, the superseded row 21 gone |
| 21a status BLOCKED | yes | line 59 reads `**BLOCKED**`, not PROVISIONAL |
| 21a an UPPER BOUND of ~8.3%, not "0%" | yes | "0 events in 36 trials. By the rule of three the 95% upper bound is 3/36, approximately **8.3%**. ***It is not 0%.***" |
| 21a records n=200 chosen, not derived | yes | "**The n = 200 the superseded row specified was chosen and not derived.**" and the derivation named as the blocked thing |
| 21b status PROVISIONAL, route coverage, never a rate | yes | line 60, "5 of 6 routes closed", "**Coverage, and never a rate**" |
| §12.1 row for the split | yes | P85 in `docs/spec/from_narrative_to_null_v1_14.md` |
| ratification draw command | yes | `python -m fntn.scanner ratify-draw`, `cli.py:509`; reveal at `cli.py:519` |
| draw file with labels withheld | yes | `docs/ratification_draw_2026-08-27.md`, tracked |

Nothing outstanding.

## 5. COMMIT 2, the run report: **LANDED, complete**

```
$ python -m fntn.scanner --help
  {init,markets,template,check,trace,ratify-draw,ratify-reveal,report,sweep}
    report              write the run report from the ledger (§9.2)
```

| Required | Found | Evidence |
|---|---|---|
| `report` subcommand | yes | `cli.py:527`, in `--help` above |
| `docs/runs/` exists and is tracked | yes | `git ls-files docs/runs/` returns `docs/runs/2026-08-27_funnel.md` |
| queue ordering test | yes | `test_the_queue_is_ordered_by_outstanding_count_and_nothing_else` (`tests/test_scanner.py:2600`) |
| no-other-ranking-key test | yes | `test_the_report_carries_no_ranking_key_other_than_the_count` (`:2640`) |
| ordering robust to ledger order | yes | `test_the_queue_ordering_survives_a_reversed_ledger` (`:2682`) |
| §12.1 row | yes | P86 |

Nothing outstanding. Phase 2 re-runs the command against the current state, so
that the committed report describes the tree as it now stands.

## 6. COMMIT 3, the intake budget: **LANDED IN THE CODE, INCOMPLETE IN THE REGISTER**

The code, the reason code, the tests and the change-log row are all present:

| Required | Found | Evidence |
|---|---|---|
| `intake_point_budget_s` | yes, 20.0 | `params.py:174` |
| `intake_subject_budget_s` | yes, 120.0 | `params.py:178` |
| `budget_retry_max` | yes, 1 | `params.py:183` |
| reaches the hash | yes | re-stamped to `ce576a9fa04a7403`, causing field `intake_point_budget_s` |
| reason code `intake_budget_exhausted` | yes | `codes.py:155`, `refuse_to_score` |
| non-positional, kept out of row 23 | yes | `codes.py:885`, `INTAKE_NON_POSITIONAL` |
| replay-determinism test | yes | `test_a_replay_under_a_different_wall_clock_reproduces_the_decision` (`tests/test_scanner.py:2878`), which hands `ReplayedBudget` a clock that raises if touched |
| abandonment count printed including zero | yes | `docs/runs/2026-08-27_funnel.md:26`, "abandoned to intake budget: **0**" |
| §12.1 row applying the §0.6 test explicitly | yes | P87, "**§0.6 applied explicitly, and the answer recorded** ... it is a **restriction**" |
| `REGISTRATION_HISTORY.md` row for the new hash | yes | row 5, `ce576a9fa04a7403`, causing field `intake_point_budget_s` |

**What is missing.** The instruction's last clause on commit 3 was to *update
rows 19, 20, 21a and 21b to name the new hash, distinguishing as P80 did
between the commitment moving and the object being re-stamped*. It did not
land:

```
$ grep -n "ce576a9fa04a7403" docs/OPEN_ITEMS.md
65: | 27 | **Intake budget** | ...
```

Only row 27, the budget's own row, names `ce576a9fa04a7403`. Rows 19, 20, 21a
and 21b still name `701adbd9d48015ed` as the most recent stamp on the objects
carrying δ, *n*ₘᵢₙ, the ratio, the seed and the fence readings.

**Why this matters and why it is not merely tidying.** Rows 19 and 20 carry the
control-arm commitment and say in terms that it *has not moved*. The sentence
that makes that claim readable is the one naming the current hash and the field
that caused it. With `701adbd9d48015ed` named as the latest, a reader
reconciling row 19 against `discovery_registration.json` finds a hash the row
does not mention and cannot tell, from the row alone, whether the commitment
moved with it. **That is the exact confusion P80 introduced the
commitment-versus-object distinction to prevent**, and the rows are one
re-stamp out of date with respect to it. This is the only outstanding item and
Phase 1 lands it.

## 7. The integrity check (0d): **PASSES**

```
$ python -m pytest tests/ -q -k registration_history
1 passed, 217 deselected in 0.52s
```

Asserted by hand, not merely by the test:

**Every hash in `docs/OPEN_ITEMS.md` appears in `docs/REGISTRATION_HISTORY.md`.**
Both files yield the same set of five:

```
701adbd9d48015ed  890a80e3a8566837  a06400ef28ebb54c  b8dd61e7eea6898e  ce576a9fa04a7403
```

**Every hash in `discovery_registration.json` is accounted for.** The file
carries two sixteen-character values:

```
"registered_hash":   "ce576a9fa04a7403"   -> row 5 of the history
"registered_schema": "cb1dffbfadbe3d58"   -> not a registration hash
```

`cb1dffbfadbe3d58` is the **schema fingerprint**, a digest of the field names
the hash is taken over, and it is correctly absent from the history, which is a
chain of registration hashes. It is recorded here because a mechanical sweep
for sixteen hex characters finds it and it reads at first glance as an
unrecorded stamp. It is not one.

> *Superseded later on 27 August 2026, and the paragraph above is left standing
> as the reason.* Needing a paragraph to tell a reader that one of two
> identically shaped values is not a stamp is a check only a person can
> complete. The fingerprint is now stored **typed**, as
> `schema:cb1dffbfadbe3d58`, and the sweep is written down in
> `docs/REGISTRATION_HISTORY.md` as
> `(?<![:0-9a-fA-F])[0-9a-f]{16}(?![0-9a-fA-F])`, which yields the registration
> hash and not the fingerprint. What this section found stands; the sweep it
> used does not, and running the old naked `[0-9a-f]{16}` against the file today
> would still find the digest under the prefix.

**The stored hash recomputes**, and under the schema it was taken under:

```
stored    : ce576a9fa04a7403
recomputed: ce576a9fa04a7403          MATCH
schema stored : cb1dffbfadbe3d58
schema current: cb1dffbfadbe3d58      MATCH
```

**The anticipated failure did not occur.** Phase 0d warned that a half-landed
commit 3 might have re-stamped the registration whilst leaving no history row.
It did not: row 5 exists, names `intake_point_budget_s` as the causing field,
and carries provenance `verified_primary`. Row 5's object commit reads
**current** rather than a SHA, which is correct under this file's own rule: the
row is completed with its SHA at the moment it is superseded, because the
commit carrying an object does not exist until the commit is made.

No history row is missing. Nothing had to be repaired before proceeding.

## 8. What Phase 1 has to do

One item: name `ce576a9fa04a7403` on rows 19, 20, 21a and 21b, with the causing
field, and preserve on each the distinction between the commitment moving and
the object being re-stamped. It is a correction to a *record of a rule change*,
not to a rule, so it is not itself a new version and takes no §12.1 row.
