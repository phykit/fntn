# Reconciliation, 27 August 2026, fourth pass

Written **before** any work in the delegated-authority batch, under CLAUDE.md's
session protocol. Each statement names the command that establishes it.

## 1. Tree, branch, push state

```
$ git status --porcelain                                    (empty)
$ git rev-parse --abbrev-ref HEAD                           fence-and-corpus-repairs
$ git log --oneline origin/fence-and-corpus-repairs..HEAD   (empty)
$ python -m pytest tests/ -q                                265 passed
```

**Clean, nothing unpushed on the working branch, 265 passing.**

## 2. One drift found, and it is the count in CLAUDE.md

`CLAUDE.md` line 137 reads `# 264 tests`. The suite is **265**: the resumed
batch added `test_row_23_splits_the_control_arm_from_the_agent_arm` in phase 6.
**Corrected in this pass**, and recorded here rather than fixed silently,
because a count in a project instruction file is exactly the kind of number
that drifts and is then quoted.

## 3. `origin/main` is eight commits behind, again

```
$ git rev-list --count origin/main..HEAD    8
$ git log --oneline -1 origin/main          2ad903a Phase 1: the 1e residual ...
```

**This reproduces the finding the third pass recorded.** Phase 0 of the
previous batch merged and main has fallen behind again in the eight commits
since. *The corollary that pass added stands: a commit pushed to a branch
nothing watches is not a record.* **Phase 0 of this batch merges again**, and
phase 9c merges a second time so the batch does not end in the state it began
in.

## 4. What this batch is, and the one thing it is not

**The operator has delegated the PREPARED recommendations.** Where a decision
was prepared with a recommended value, it is taken on delegated authority and
recorded as such, dated 27 August 2026, with the operator's standing right to
revise.

**The delegation does not extend to phase 6b**, the §0.10 and §7.6
promotion-to-live-capital predicate. That predicate governs when real capital is
deployed, no recommendation for it has been prepared, and it opens as a §13 row
BLOCKED on an explicit §0 decision. **Nothing in this batch authorises capital.**

## 5. What is expected to re-stamp

Two phases move the registration hash: **2a** (row 29 enters the parameter
object) and **5e** (`audit_fraction` does). `docs/REGISTRATION_HISTORY.md` row 5
must have its object commit completed before `save` will overwrite, which is
what that column is for. **Rows 21a and 21b name the hash their readings were
TAKEN UNDER and do not move.**
