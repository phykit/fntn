# Coding conventions

Every convention here is a spec rule with an implementation consequence. Each states the rule, the code shape it implies, and the failure it prevents. Where a convention seems fussy, the third column is why it is not.

---

## Refusals

**Reason codes live in `src/fntn/scanner/codes.py` and nowhere else.** A `ReasonCode` carries its surface, a description, a §8 summary template, a resurrection predicate, and a `refuse_to_score` flag.

```python
# WRONG: a code invented at the site of use
return ("weird_input", {...})

# RIGHT: registered, with its template and predicate, then emitted
# codes.py
ReasonCode(code="issuer_unresolved", surface=Surface.OBSERVATION, ...)
```

`summaries.render()` raises on an unregistered code, and `codes.coverage()` raises if an emitted code is not in the registry. *A kill that cannot be counted cannot be shown to have been reached*: this is the §9.4 failure class, enforced at the type level rather than by discipline.

**Every refusal writes.** An abort that writes nothing shrinks §7.1's denominator silently. Fail-fast is a compute discipline, never a bookkeeping one.

**Summaries are rendered, never generated.** A model-written account of a deterministic decision is a probabilistic gloss on an exact fact. Where the deciding step was human, `summaries.operator_authored()` requires the operator's own two to three sentences and records the author.

## No fallbacks

The single most common way this codebase can be silently broken is a sensible-looking default.

```python
# WRONG, in four different ways
value = extracted.get("direction") or "long"
theta  = config.theta if config.theta else 0.25
try:    rate = compute()
except: rate = 0.0
count = max(1, configured_count)      # silently repairs a broken config
```

Each of these converts *I do not know* into *here is a number*, and the number then travels with no tag saying where it came from. The correct shape is a refusal with a code, or a raise:

```python
if not ctx.entity_fence.security_master:
    return ("security_master_unavailable", {})
if config.control_arm_ratio <= 0:
    raise ValueError("a discovery layer with no control arm has no instrument that can refute it")
```

**A not-applicable check is recorded and never read as a pass.** See `check_not_applicable_pointer_tier`.

## Determinism

- Model calls: schema-enforced, temperature zero, cached by content hash.
- No network at decision time. Retrieval happens before the checks run, so no check performs I/O.
- Anything sampled must be replayable: the audit stream is a hash of `(parameter_hash, surface, subject_id)`, the control arm draw is seeded, and both seeds are pre-registered. *A control redrawn after the treatment's result is known is not a control.*
- Ordered check sequences are declared explicitly in `codes.py`, not derived from definition order, so tidying a file cannot change the reason-code distribution.

## Fences

Four, and they are different kinds of object. Do not weaken any of them to make a test pass.

| Fence | Kind | Enforced by |
|---|---|---|
| Authority | schema | reserved fields are **absent from `Proposal`**, not present and validated |
| Entity | lookup | security master and listing lists; patterns only for closed grammars |
| Query | audit log | conditional-return queries refused, not merely recorded |
| Import | static | transitive import closure, checked at process start and in tests |

**The strongest form of a fence is a field that does not exist.** Prefer removing the field over validating it: a field that exists can be filled by a future caller who has forgotten why it was reserved.

## Tests

- `test_every_defined_code_is_emitted` is the headline. Add a code, add its branch, add the test that reaches it, in one commit.
- Test the *reason*, not just the behaviour. `test_fence_runs_before_retrieval` asserts an ordering property that a coverage number would not catch.
- **Unit tests are the weaker instrument.** The pattern-only entity fence passed every unit test and refused 94% of real agent proposals. Before claiming a fence works, run `src/fntn/scanner/trace.py` over real material.

## Ledger

SQLite, keyed on parameter hash and subject. **Nothing is deleted and nothing is overwritten.** `rejection_summary` sits in a column no query joins on, which is what makes it structurally display-only: a badly written summary can mislead a reader and cannot mislead the system.

## Naming

Use the spec's names, exactly. `issuer` and `instrument_referenced` are canonical; `issuer_id` / `instrument_id` are superseded and the parameter object carries no alias. One extraction field named three ways across three artefacts was a must-class defect found by the review harness, and renaming to taste re-creates it.

## Comments

Docstrings carry the *reason* a rule exists. Compare:

```python
# Useless: restates the code
# Refuse if there is no security master.

# Useful: survives contact with someone who wants to remove it
# Patterns alone are not a fence: the pattern-only version refused 94% of real
# agent proposals because a regulator's name and an issuer's name are both
# proper nouns. Without a master the binding layer cannot run, so this refuses
# to score rather than passing on the weaker half.
```

*A rule whose justification is not written down gets relaxed by whoever meets it next.* This project's own history is the evidence: an exit rule that fired on its own entry event, a universe rule with no enforcing gate, a permissive default that became a fast lane. None was caught by re-reading.

## Style

Formal British English. **No em-dashes**, in code comments, docstrings or documents; empty table cells read `n/a`. State costs rather than benefits when recording a decision.
