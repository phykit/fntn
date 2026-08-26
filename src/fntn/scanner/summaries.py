"""§8 rejection summaries: rendered, never judged.

Two to three sentences of plain language on every refusal in the system.  For
deterministic refusals the summary is composed by a fixed template over the
record's own fields -- no model call, because a model-written account of a
deterministic decision would be a probabilistic gloss on an exact fact and the
clerk holds no authority here.  Where the deciding step was human, the operator
writes the sentences and the ledger records the author beside the text.

The summary is display-only by construction.  Nothing in this package reads one
back, and the ledger stores it in a column no query joins on.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Mapping

from .codes import ALL_CODES
from .records import Refusal


class _Defaulting(dict):
    """Renders a missing field as an explicit placeholder rather than raising.

    A refusal whose summary cannot render is still a refusal, and losing the
    record to a formatting error would be the worst possible trade.  The
    placeholder is deliberately ugly so that a missing field is visible in the
    ledger rather than reading as prose.
    """

    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
        return f"[{key} not recorded]"


def render(code: str, subject_id: str, fields: Mapping[str, object]) -> Refusal:
    """Compose the refusal record and its rendered summary."""

    if code not in ALL_CODES:
        raise ValueError(
            f"{code!r} is not in the reason-code registry; a refusal emitted "
            "from outside the registry cannot be counted"
        )
    rc = ALL_CODES[code]
    payload: Dict[str, object] = dict(fields)
    payload.setdefault("resurrection", rc.resurrection)
    summary = rc.summary_template.format_map(_Defaulting(payload))
    return Refusal(
        code=code,
        subject_id=subject_id,
        surface=rc.surface.value,
        fields=dict(fields),
        summary=summary,
        author="template",
        at=datetime.now(timezone.utc),
    )


def operator_authored(
    code: str, subject_id: str, text: str, author: str, fields: Mapping[str, object]
) -> Refusal:
    """A refusal whose deciding step was human.

    §8 requires the operator's own two to three sentences where the decision
    was theirs -- an operator-mapping refusal, a pre-mortem refusal, a directive
    displacement, a manual-acceptance decline.  The template is not offered as a
    substitute, because a rendered sentence would attribute a machine's account
    to a person's decision.
    """

    if code not in ALL_CODES:
        raise ValueError(f"{code!r} is not in the reason-code registry")
    stripped = " ".join(text.split())
    sentences = [s for s in stripped.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if not 2 <= len(sentences) <= 4:
        raise ValueError(
            "an operator-authored rejection summary is two to three sentences; "
            f"got {len(sentences)}"
        )
    return Refusal(
        code=code,
        subject_id=subject_id,
        surface=ALL_CODES[code].surface.value,
        fields=dict(fields),
        summary=stripped,
        author=author,
        at=datetime.now(timezone.utc),
    )
