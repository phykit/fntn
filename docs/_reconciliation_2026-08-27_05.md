# Reconciliation, 27 August 2026, fifth pass

Written **before** any work in the nine-phase batch, under CLAUDE.md's session
protocol. Each statement names the command that establishes it.

## 1. Tree, branch, push state

```
$ git status --porcelain                                    (empty)
$ git rev-parse --abbrev-ref HEAD                           fence-and-corpus-repairs
$ git log --oneline origin/fence-and-corpus-repairs..HEAD   (empty)
$ git rev-list --count origin/main..HEAD                    0
$ python -m pytest tests/ -q                                268 passed
```

**Clean, nothing unpushed, `main` level with the working branch, 268 passing**,
matching `CLAUDE.md`. *The previous batch ended by merging, so for the first
time in three passes this one does not open on a `main` that is behind.*

## 2. The register agrees with the code

| Claim | Established by |
|---|---|
| §13 row 1: **PROVISIONAL** | the register's own row |
| §13 row 29: **CLOSED** | the register, and `max_tolerable_fixed_cost_bps` = 10.0 in the registration |
| §13 row 31: **BLOCKED** | the register |
| Registration hash `fcfa57a15a011b33`, **verified** | `Registration.load` |
| `theta` = 0.2, `audit_fraction` = 0.1 | the registration object |

## 3. One thing that looks like a discrepancy and is one

**`delta_min_floor` is registered at 25.0 and §14's δₘᵢₙ floor cell reads
OPEN.** A value is in the parameter object and the decision that governs it is
recorded as not taken.

*That is not an error in either place.* The registered 25.0 entered as a
working value with a stated justification (the cheapest §5.2.2 break-even), and
§14 records that **nobody has decided it**. **Phase 1b is where the two are
meant to be reconciled**, by deriving the floor rather than confirming the
number that happens to be there. **It is named here so that phase 1b cannot
quietly read the registered value back as its own answer.**

## 4. What this batch can and cannot reach

```
$ echo $SEC_CONTACT                                         (unset)
$ curl -o /dev/null -w '%{http_code}' https://example.com    200
$ curl -o /dev/null -w '%{http_code}' -A 'Mozilla/5.0' \
      https://www.interactivebrokers.co.uk/.../commissions-stocks.php   200
```

- **`SEC_CONTACT` is UNSET**, so **phase 3 refuses at 3a** and goes to 3d. No
  filing is fetched and no placeholder is substituted.
- **The network is reachable and IBKR's pricing pages now answer 200.** The
  previous batch recorded a **403** on `commissions-spot-currencies.php` and
  recorded that nobody had read the page. *That refusal stands as the record of
  what was true then; this pass may read what it can now retrieve, and must say
  which pages it actually read rather than which it tried.*

## 5. The one thing this batch may not do

**§13 row 31, the promotion-to-live-capital predicate, stays BLOCKED with its
blanks empty.** The delegation over prepared recommendations does not reach it,
no recommendation exists for it, and **nothing in this batch authorises
capital.**
