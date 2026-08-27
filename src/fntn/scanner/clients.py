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

    model: str = "claude-opus-4-6"
    max_tokens: int = 8000
    api_key: Optional[str] = None
    _client: Any = None

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
        try:
            client.models.retrieve(self.model)
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
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return dict(block.input)
        raise ClientRefusal(
            "the model returned no schema-conforming block. Refusing to parse "
            "prose into a record: the clerk's output is an input to arithmetic "
            "and an unparsed guess is not one."
        )


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
