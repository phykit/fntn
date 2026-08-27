# Reconciliation, 27 August 2026, sixth pass

Written **before** any work in the eleven-phase batch, under CLAUDE.md's session
protocol.

## 1. Tree

```
$ git status --porcelain                                    (empty)
$ git log --oneline origin/fence-and-corpus-repairs..HEAD   (empty)
$ git rev-list --count origin/main..HEAD                    0
$ python -m pytest tests/ -q                                270 passed
```

**Clean, pushed, `main` level, 270 passing**, matching `CLAUDE.md`.

## 2. Register against code

| Claim | Established |
|---|---|
| Registration `eb3bbe92c34d1e6f`, **verified** | `Registration.load` |
| tolerance 10.0, δₘᵢₙ floor 17.0, θ 0.2 | the parameter object |
| discoverable classes | `insider_dealing`, `major_holdings_change`, `buyback`, `earnings_event` |
| binding path | steps **1 and 3 CLOSED**, 2, 4 and 5 not |
| `SEC_CONTACT` | **UNSET** |

## 3. What this batch changes about the project's own premises

**Three operator decisions arrive in phase 0 and each invalidates arithmetic
that is currently on the register.**

- **No live capital**, the objective being realistic backtesting. Row 31 becomes
  blocked **by decision** rather than by omission.
- **Base currency USD**, so **there is no per-trade FX conversion**. Row 1's
  absolute term loses **USD 4.00 of its USD 6.00**, and everything derived from
  that USD 6.00 moves: row 30's floors, row 29's lower bound, and δₘᵢₙ through
  row 29's bound.
- **Insider dealing is retired**, which strands `corpora/us`, the Form 4 block,
  and the only route §13 row 15 has ever had.

***This pass records in advance that phases 1c and 1d are re-derivations of
numbers this project set eleven and nine hours ago.*** *A parameter set on an
input that has since changed is not wrong for having been set; it is wrong to
leave it standing.*

## 4. The Class I invariant binds this batch

**A decision may not be taken over a caveat its own preparation states.** Where a
recommendation in this batch qualifies itself, the recommendation stops and is
reported instead. **Six instances of that class now exist**, the sixth arriving
in phase 0d, which means the invariant installed last batch was installed
against a class **still generating instances** — and phase 9b must say whether
it would have caught this one.

## 5. What may not happen

**§13 row 31 stays BLOCKED with its blanks empty. Nothing in this batch
authorises capital**, and after phase 0a that is a decision on the record rather
than a gap in one.
