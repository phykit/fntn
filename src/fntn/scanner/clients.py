"""Concrete `AgentClient` implementations.

`discovery.sweep` takes any object with `complete(system, user, schema) -> dict`.
Two are provided:

* `AnthropicClient`, which calls the API with the schema attached as a forced
  tool call, so the model cannot return prose where a record is required. It is
  NOT a temperature-zero call: see its docstring.
* `TranscriptClient`, which replays a saved payload. A sweep whose proposals
  came from a file is legible and free, and it is what the trace harness should
  normally be pointed at.

**Note the fence this module does not enforce and cannot.** The import fence
covers what the discovery *code* can reach. It says nothing about what the
*model* can reach: an agent given web search, a database tool or a file reader
can look up prices whatever the import graph says. A production client must
therefore expose **no tools at all**, which is why `AnthropicClient` sends none
and refuses to accept any. If you wire a tool-using agent into this interface,
the exclusivity construction of §3.7.3 is void and every directive it raises is
`self_generated` evidence about a search you can no longer characterise.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


class ClientRefusal(RuntimeError):
    pass


@dataclass
class AnthropicClient:
    """Schema-enforced, no tools, and NO LONGER temperature zero.

    Requires the `anthropic` package and a **usable** API key. Both are checked
    at construction rather than at first call, so a misconfiguration surfaces
    before a sweep is half-run.

    ***Two things this class claimed on 27 August 2026 and did not do.***

    **One: it did not check that the key WORKS.** It tested ``if not key``, so
    an environment variable set to a ten-character stub passed construction and
    the sweep failed at the API. *A variable that is SET is not thereby USABLE,
    and the same defect was live in `trace_filings.user_agent` on the same day.*
    **The check is now a preflight call** to ``models.retrieve``, which costs no
    tokens and settles the key and the model identifier together. *A shape or
    length test was considered and rejected: it would encode a guess about how
    keys are formatted, and the question is not what the key looks like.*

    **Two: temperature zero is no longer available.** ``messages.create`` in
    `anthropic` 1.x does not accept ``temperature`` at all, and the current
    models reject sampling parameters with a 400. The call carried
    ``temperature=0`` and raised ``TypeError`` before it ever reached
    authentication.

    ***What was lost with it, and what never rested on it.*** **Lost:** two
    sweeps over identical material may now return different proposals.
    **Not lost, and this was checked rather than assumed:** replay is served by
    `TranscriptClient` reading a saved payload, `ProposalCache` is keyed on the
    content hash of the prompt and not on the reply, and the control arm is
    drawn from a registered seed with no model in its path. **Rule 1's
    guarantee is over LOGGED data and is untouched.** *Run-to-run stability was
    a convenience the docstring oversold as determinism.*
    """

    #: **No default, deliberately.** The pin is a registered field (§13 row 39)
    #: and a default here is a second copy of it that no hash covers: a sweep
    #: could run under a model the registration does not name and the ledger
    #: would record the wrong clerk. `cli.py` reads it from the registration
    #: and from nowhere else.
    model: str
    max_tokens: int = 8000
    api_key: Optional[str] = None
    _client: Any = None
    #: What the preflight established, so a caller can print it rather than
    #: re-derive it. See `__post_init__`.
    _preflight: Any = None
    #: Cumulative usage over every call this client has made. Counted because
    #: the budget is small and was unmeasured, and because a cost figure
    #: recovered afterwards from a dashboard is a different number from the one
    #: the run itself observed. Read from ``response.usage`` and from nothing
    #: else; a field the API does not return is counted as absent and not as
    #: zero (see ``spend``).
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    #: Set when a usage block arrived without one of the two billed counters.
    #: A missing counter makes the cost a LOWER BOUND rather than a figure, and
    #: the distinction is carried rather than smoothed away.
    usage_incomplete: bool = False

    def __post_init__(self) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:  # pragma: no cover - environment
            raise ClientRefusal(
                "the anthropic package is not installed, so no sweep has run "
                "and none has failed. Install it with `pip install anthropic`."
            ) from exc
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ClientRefusal(
                "no API key: set ANTHROPIC_API_KEY or pass api_key. Refusing "
                "rather than falling back to an unauthenticated call that would "
                "fail later with a less useful message."
            )
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        # The preflight. One call, no tokens, and it settles the key and the
        # model together. Refused rather than deferred: a sweep that discovers
        # at document 40 that it was never authenticated has spent forty
        # documents' worth of nothing and reports it as a failure of the sweep.
        #
        # **It ENUMERATES rather than retrieving** (P137). `models.retrieve`
        # answers *is this id resolvable*; `models.list` answers *what does
        # this key actually have*, and the refusal can then name the
        # alternatives instead of leaving the operator to guess. **Four
        # separate failures -- an absent key, a stub key, a model question
        # settled from a cached table, and a sweep that could not have run --
        # were each found only by running the whole thing**, so the preflight
        # is deliberately the widest cheap check available rather than the
        # narrowest sufficient one.
        try:
            available = [m.id for m in client.models.list(limit=100).data]
            if self.model not in available:
                raise ClientRefusal(
                    f"the pinned model {self.model!r} is NOT in the models "
                    f"this key can see.\n\n"
                    f"Available: {', '.join(sorted(available)) or '(none)'}\n\n"
                    "REFUSED rather than substituting one. Which model read "
                    "the corpus is part of what a proposal is replayable "
                    "against, so a pin that silently moves makes two sweeps "
                    "incomparable without saying so."
                )
        except anthropic.AuthenticationError as exc:
            raise ClientRefusal(
                f"ANTHROPIC_API_KEY is set and the API refused it: {exc}.\n\n"
                "SET IS NOT USABLE. A placeholder, a revoked key and a "
                "truncated paste all satisfy a presence check and none of them "
                "authenticates, so this is checked here rather than discovered "
                "part-way through a sweep.\n\n"
                "Nothing has been swept and no proposal has been authored."
            ) from exc
        except anthropic.NotFoundError as exc:
            raise ClientRefusal(
                f"the model {self.model!r} is not available to this key: "
                f"{exc}.\n\nRefusing rather than substituting a model the "
                "operator did not choose: which model read the corpus is part "
                "of what a proposal has to be replayable against."
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise ClientRefusal(
                f"the API could not be reached: {exc}. Nothing was swept. "
                "This is reported as a network failure and NOT as an empty "
                "sweep, because the two mean opposite things."
            ) from exc
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_preflight", {
            "model": self.model,
            "models_visible": len(available),
            # **The credit state is REPORTED AS UNESTABLISHED, and that is not
            # evasion.** The models endpoint does not consult the balance, so a
            # 200 from it says the key authenticates and says nothing whatever
            # about credit. Reading "the endpoint answered" as "there is credit"
            # is a conclusion from a partial view, which is the class this
            # preflight exists because of. A low balance surfaces as a 400 on
            # the first message call, and that is where it will be reported.
            "credit": "not established by the preflight: the models endpoint "
                      "does not consult the balance. A shortfall surfaces as a "
                      "400 on the first sweep call.",
        })

    def complete(
        self, system: str, user: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """One call. The schema is forced, not requested.

        ``temperature`` is not passed: it is absent from `anthropic` 1.x's
        ``messages.create`` and rejected by the current models. See the class
        docstring for what that costs and what it does not.
        """

        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            tools=[
                {
                    "name": "emit_proposals",
                    "description": (
                        "Emit candidate mechanisms against the fixed schema. "
                        "This is the only permitted output."
                    ),
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": "emit_proposals"},
            messages=[{"role": "user", "content": user}],
        )
        self._account(getattr(response, "usage", None))
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise ClientRefusal(
            "the model returned no schema-conforming block. Refusing to parse "
            "prose into a record: the clerk's output is an input to arithmetic "
            "and an unparsed guess is not one."
        )


    def _account(self, usage: Any) -> None:
        """Accumulate one response's usage. Absent is absent, never zero.

        **Why the distinction is kept.** A cost computed over a counter the API
        did not return is not a smaller cost; it is a cost that was not
        measured. Reporting it as a number would be the refuse-to-score rule
        broken in the one place the project is spending real money, so a
        missing counter sets ``usage_incomplete`` and every figure derived from
        it is labelled a lower bound.
        """

        self.calls += 1
        if usage is None:
            self.usage_incomplete = True
            return
        for field_name in ("input_tokens", "output_tokens",
                           "cache_read_input_tokens",
                           "cache_creation_input_tokens"):
            value = getattr(usage, field_name, None)
            if value is None:
                # The two cache counters are absent on an uncached request and
                # that is not a gap. The two billed counters are.
                if field_name in ("input_tokens", "output_tokens"):
                    self.usage_incomplete = True
                continue
            setattr(self, field_name, getattr(self, field_name) + int(value))

    def spend(self) -> "Spend":
        """What this client has cost so far, at the rates in `PRICING`."""

        return Spend.of(
            model=self.model,
            calls=self.calls,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens,
            cache_creation_input_tokens=self.cache_creation_input_tokens,
            complete=not self.usage_incomplete,
        )


#: Published list prices, USD per million tokens, as (input, output).
#:
#: ***PROVENANCE, stated because a cost figure without one is a guess wearing a
#: decimal point.*** These are read from the bundled `claude-api` reference
#: table, which carries its own stamp `cached: 2026-06-24`. That makes them
#: **`named, unread`** against a live pricing page under §0.5, and every figure
#: this module derives inherits that tag. They are adequate for a spend guard,
#: whose question is *is this about to cost more than the balance*, and they
#: are NOT adequate for anything a decision is taken on.
#:
#: **Cache rates are the published multipliers on the input rate**: a cache
#: write bills at 1.25x input and a cache read at 0.1x. The sweep sets no
#: `cache_control`, so both counters are expected to be zero and are carried
#: anyway rather than assumed away.
PRICING: Dict[str, tuple] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-fable-5": (10.00, 50.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-opus-4-5-20251101": (5.00, 25.00),
    "claude-sonnet-4-5-20250929": (3.00, 15.00),
}

CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


@dataclass
class Spend:
    """One client's measured token usage and what it costs at list price.

    ``usd`` is ``None`` when the model is not in `PRICING`. **It is not zero
    and it is not a guess**: a model whose rate is unknown produces a refusal
    to score, which is rule 3 applied to the one quantity the operator is
    actually spending.
    """

    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    complete: bool
    usd: Optional[float]
    rate: Optional[tuple]

    @classmethod
    def of(cls, model: str, calls: int, input_tokens: int, output_tokens: int,
           cache_read_input_tokens: int, cache_creation_input_tokens: int,
           complete: bool) -> "Spend":
        rate = PRICING.get(model)
        usd = None
        if rate is not None:
            rin, rout = rate
            usd = (
                input_tokens * rin
                + cache_creation_input_tokens * rin * CACHE_WRITE_MULTIPLIER
                + cache_read_input_tokens * rin * CACHE_READ_MULTIPLIER
                + output_tokens * rout
            ) / 1_000_000
        return cls(model=model, calls=calls, input_tokens=input_tokens,
                   output_tokens=output_tokens,
                   cache_read_input_tokens=cache_read_input_tokens,
                   cache_creation_input_tokens=cache_creation_input_tokens,
                   complete=complete, usd=usd, rate=rate)

    def render(self, label: str = "spend") -> str:
        lines = [
            f"{label}: {self.calls} model call(s) at {self.model}",
            f"  input tokens          : {self.input_tokens}",
            f"  output tokens         : {self.output_tokens}",
        ]
        if self.cache_creation_input_tokens or self.cache_read_input_tokens:
            lines.append(
                f"  cache write / read    : {self.cache_creation_input_tokens}"
                f" / {self.cache_read_input_tokens}"
            )
        if self.usd is None:
            lines.append(
                f"  cost                  : NOT SCORED. {self.model!r} is not "
                "in the price table, and a rate that is not known is not zero."
            )
        else:
            bound = "" if self.complete else "  (LOWER BOUND: a usage counter was absent)"
            lines.append(f"  cost at list price    : USD {self.usd:.4f}{bound}")
            lines.append(
                f"  rate                  : USD {self.rate[0]:.2f} in / "
                f"{self.rate[1]:.2f} out per 1M, list, provenance "
                "`named, unread` (cached table, 2026-06-24)"
            )
        return "\n".join(lines)


@dataclass
class TranscriptClient:
    """Replays a saved payload. Deterministic, free, and auditable.

    Point the trace harness at this. A sweep replayed from a transcript exercises
    the whole ingestion path without a network call and without spending a live
    model call on machinery that is being tested rather than used.
    """

    path: str
    _payloads: Optional[list] = None
    calls: int = 0

    def complete(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        if self._payloads is None:
            raw = json.loads(open(self.path, encoding="utf-8").read())
            # Accept either a bare payload or the trace-corpus shape.
            if "sweeps" in raw:
                object.__setattr__(
                    self, "_payloads",
                    [{"proposals": s.get("proposals", [])} for s in raw["sweeps"]],
                )
            else:
                object.__setattr__(self, "_payloads", [raw])
        self.calls += 1
        if not self._payloads:
            return {"proposals": []}
        return self._payloads.pop(0)
