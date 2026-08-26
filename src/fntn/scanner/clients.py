"""Concrete `AgentClient` implementations.

`discovery.sweep` takes any object with `complete(system, user, schema) -> dict`.
Two are provided:

* `AnthropicClient`, which calls the API at temperature zero with the schema
  attached as a forced tool call, so the model cannot return prose where a
  record is required.
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
    """Schema-enforced, temperature zero, no tools.

    Requires the `anthropic` package and an API key. Both are checked at
    construction rather than at first call, so a misconfiguration surfaces
    before a sweep is half-run.
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

        object.__setattr__(self, "_client", anthropic.Anthropic(api_key=key))

    def complete(
        self, system: str, user: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """One call. Temperature zero. The schema is forced, not requested."""

        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
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
