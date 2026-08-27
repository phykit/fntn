# Prepared, NOT taken: enforcing the proposal schema at the API

**27 August 2026 (P137). Addressed to the operator.** *Prepared under the
delegation and deliberately left, because the §0.6 test does not come out
clean and the answer turns on what the authority fence is FOR.*

---

## What is on the table

**Today.** `AnthropicClient.complete` attaches the proposal schema as a
**forced tool call** — `tool_choice={"type": "tool", "name": "emit_proposals"}`
— so the model must answer in the tool's shape. **The shape is requested and
then parsed.** Nothing at the API rejects a response carrying fields outside
the declared schema; `fences.raw_payloads` is what would catch that, and intake
point 1, `agent_overreached_schema`, is the code it emits.

**The change.** Set **`strict: true`** on the tool definition, with
`additionalProperties: false` and `required` in the schema. The API then
validates `tool_use.input` against the schema server-side and **an
out-of-schema response cannot be returned at all.**

*A second, separate mechanism exists — `output_config.format` on the message —
and is not proposed here: the proposals arrive as a tool call, and mixing the
two would give the same object two enforcement points.*

---

## THE COST, STATED BEFORE THE BENEFIT

> ***It would make intake point 1 unreachable BY CONSTRUCTION.***

`docs/INTAKE_POINTS_2026-08-27.md` records `agent_overreached_schema` as
unreachable today, and is precise about why: **`raw_payloads()` is called from
nowhere**, so nothing is ever offered to it. **That is a WIRING DEFECT, and a
wiring defect can be repaired.** *If the API enforces the schema, the point
becomes unreachable for a second and permanent reason, and repairing the wiring
would no longer make it reachable.*

**Why that matters more than it looks.** `CLAUDE.md`'s headline test is
`test_every_defined_code_is_emitted`: **a code defined but never emitted is an
untested branch.** A code that can *never* be emitted is worse — it is a fence
the project believes it has. **The honest options if `strict` is taken are to
retire the code, or to keep it and record that the API now holds that line**,
and *the second is only honest if the API's guarantee is actually stronger than
the fence's, which nobody here has established.*

**And it moves a fence off this tree and onto a supplier.** The authority fence
is one of the four §3.7 fences. Under `strict` the guarantee is the API's, it
is versioned by the supplier, it is not in the parameter object, and **it
cannot be traced by `trace.py`.** *Rules read against a world are the stronger
instrument, and `strict` removes the world this particular rule is read
against.*

## The benefit, which is real

- **A malformed response cannot enter the ledger**, rather than entering it and
  being refused one intake point later.
- **The refusal moves from the consumer to the producer**, which is where this
  project puts refusals everywhere else.
- **It costs nothing per call** and no beta header.

---

## §0.6, applied explicitly, with the answer recorded

**The test.** *Does it add a gate, a family, a grammar row, a cost tier, a
sizing input, a feed, or a field the funnel reads at decision time?*

| Element | Added? |
|---|---|
| Gate | **no** |
| Family | **no** |
| Grammar row | **no** |
| Cost tier | **no** |
| Sizing input | **no** |
| Feed | **no** |
| Field read at decision time | **no** |

> ***ANSWER: it is NOT apparatus. §0.6 does not block it.***

***And it is not thereby free.*** It is an **admissibility rule** — what the
funnel will accept as a proposal — and **rule 5 counts an admissibility change
as a specification version**, so it takes a `§12.1` row whichever way it goes.
*The `schema_matches` widening at P87a is the precedent, and that row records
how close such a call can be.*

**Which direction is it?** ***A restriction.*** The set of admissible responses
narrows. *That is why §0.6 clears it, and it is also why the cost above is the
part worth arguing about: the thing it narrows away is the material the
authority fence exists to catch.*

---

## The recommendation, and it is to WAIT

**Not on grounds of merit. On grounds of ORDER.**

1. ***No sweep has ever run.*** **Zero proposals have been drawn**, so nothing
   is known about whether models return out-of-schema material against this
   prompt at all. **Enforcing a shape before observing one instance of it is
   choosing a remedy for an unmeasured problem** — which is the move this
   project exists to refuse.
2. ***The first sweep is the measurement.*** If `raw_payloads` is wired and one
   block is swept, **intake point 1 either fires or it does not**, and that is
   a §13-row-shaped fact about how often the clerk overreaches. **`strict`
   taken afterwards costs a known quantity; taken now it costs an unknown
   one.**
3. **Taking it later is cheap.** One field on the tool definition, one `§12.1`
   row. **Nothing about waiting makes it harder.**

> ***RECOMMENDED: wire `raw_payloads`, run one sweep, read intake point 1, and
> decide then. If the operator prefers the API to hold the line regardless,
> that is a defensible call and the cost is the paragraph above.***

**Whichever way it goes, one thing is not optional:** *if `strict` is taken,
`agent_overreached_schema` must be either retired or explicitly re-based on the
API's guarantee, in the same commit.* **A reason code that cannot fire, left in
the registry saying nothing, is a fence the project believes it has.**
