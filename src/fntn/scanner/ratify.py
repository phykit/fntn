"""§13 row 21a's ratification harness: put the clerk's labels in front of a person.

**What this is for.** Rows 21a and 21b both read against `docs/labelled_proposals.json`,
whose labels carry provenance ``model_clerk``.  Those are the clerk's
classifications against the fixed taxonomy, not the operator's, and CLAUDE.md's
first rule says the model classifies whilst the table decides.  A reading taken
against labels the model wrote and nobody checked is a reading of the model
against itself.  This harness is the check, and it is **procedure**: it adds no
gate, no family, no grammar row and no field the funnel reads at decision time,
and it produces a document for a person rather than a verdict for a machine.

**The draw is not chosen.**  Twelve of the thirty-six drawn-arm subjects, by the
registered seed.  Whoever runs it cannot steer which twelve, cannot re-run until
a comfortable set appears, and cannot claim afterwards that the set was
representative: the same registration produces the same twelve every time, and a
different twelve requires a re-stamp with the causing field named.

**The label is withheld and that is the whole design.**  An operator shown the
clerk's answer beside the question is being asked to agree, not to label, and
agreement obtained that way measures the operator's deference rather than the
clerk's accuracy.

**The rule the harness enforces on itself, stated before any result exists: one
disagreement in twelve refutes the clerk's labels for the whole arm.**  Not
"reduces confidence in", not "is noted alongside".  §13 row 21a's reading is
0 of 36 refused, and every one of those 36 verdicts is the fence's verdict
compared against a clerk label; if the clerk and the operator part company on
any subject, the labels are not the operator's classifications and the arm has
no denominator anyone has checked.  Twelve is a third of the arm, so a single
disagreement implies roughly three across it, which is the size of the finding
the whole reading is about.  This is stated here, before the draw, because a
threshold written after the answer is known is not a threshold.

**Both arms go in the file, and only one is withheld.**  All six authored probes
are written out unwithheld, because row 21b is not a sampling question: it asks
whether each probe exercises the route it claims and whether those are the
routes that matter, and both are answered by reading all six.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .trace import LabelledProposal, load_labelled

#: How many of the drawn arm go in front of the operator.  A third of it, which
#: is what makes one disagreement in the draw imply roughly three across the arm
#: and therefore worth the refutation rule above.
DRAW_N = 12

#: Fixed salt, so the ratification draw does not share a random stream with the
#: control arm, which is drawn from the same registered seed for a different
#: purpose.  It is a constant in code and not an input: nobody running the
#: harness can vary it, so the draw stays unchoosable whilst staying independent.
_SALT = "ratification-draw-v1"


class RatificationRefused(RuntimeError):
    """Raised rather than defaulted.  See each call site for which case."""


@dataclass
class DrawnSubject:
    subject_id: str
    event_class: str
    event_definition: str
    measured_on_intention: str
    mechanism_note: str
    corpus_id: str
    #: The clerk's label.  Written to the reveal file and never to the draw.
    clerk_is_class_level: bool
    clerk_note: str = ""


def _subjects(labelled: List[LabelledProposal]) -> Tuple[List[LabelledProposal], List[LabelledProposal]]:
    drawn = [l for l in labelled if l.is_class_level or l.probe_route == ""]
    probes = [l for l in labelled if l.probe_route]
    # The two arms are identified by what they are, not by counting on the
    # file's ordering.  An arm that came back empty would make every statement
    # about it vacuously true, which is the defect docs/CONVENTIONS.md names.
    if not drawn:
        raise RatificationRefused(
            "no drawn-arm subjects in the labelled set. Row 21a has no arm to "
            "ratify and this refuses rather than writing an empty file."
        )
    if not probes:
        raise RatificationRefused(
            "no authored probes in the labelled set. Row 21b is coverage over "
            "named routes, and a file with no routes in it covers nothing."
        )
    return drawn, probes


def draw(labelled: List[LabelledProposal], seed: int, n: int = DRAW_N) -> List[LabelledProposal]:
    """The ``n`` subjects the registered seed selects.  Deterministic.

    Refuses rather than truncating where the arm is smaller than the draw: a
    draw of twelve that silently returned nine would put a different
    denominator behind the refutation rule than the one stated for it.
    """

    drawn, _ = _subjects(labelled)
    if len(drawn) < n:
        raise RatificationRefused(
            f"the drawn arm holds {len(drawn)} subjects and the draw is {n}. "
            "Refusing to shrink the draw silently: the refutation rule is "
            "stated against a denominator, and changing it changes the rule."
        )
    rng = random.Random(f"{seed}:{_SALT}")
    return rng.sample(sorted(drawn, key=lambda l: l.subject_id), n)


def _digest(labelled: List[LabelledProposal], seed: int, n: int) -> str:
    """Ties a reveal to the draw it belongs to.

    Over the subject ids and the seed, so a reveal cannot be read against a
    draw taken from a different labelled set or a different registration.  It
    covers the question and not the answer, so it can be printed in the
    withheld file without carrying a label into it.
    """

    ids = [l.subject_id for l in draw(labelled, seed, n)]
    blob = json.dumps({"ids": ids, "seed": seed, "n": n}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def render_draw(
    labelled: List[LabelledProposal],
    seed: int,
    parameter_hash: str,
    on: date,
    n: int = DRAW_N,
) -> str:
    """The operator's worksheet.  Drawn-arm labels withheld; all probes shown."""

    picked = draw(labelled, seed, n)
    _, probes = _subjects(labelled)
    out = [
        f"# Ratification draw, {on.isoformat()}",
        "",
        f"Registration `{parameter_hash}`. Registered seed `{seed}`, salt "
        f"`{_SALT}`. Draw digest `{_digest(labelled, seed, n)}`.",
        "",
        "**The clerk's labels on the drawn arm are withheld from this file.** An "
        "operator shown the answer beside the question is being asked to agree "
        "rather than to label, and agreement obtained that way measures "
        "deference and not accuracy. Write your own label in each box, then run "
        "`python -m fntn.scanner ratify-reveal`.",
        "",
        "**Stated before any result exists: one disagreement in twelve refutes "
        "the clerk's labels for the whole drawn arm.** Not reduces confidence "
        "in them. Row 21a's reading compares the fence's verdict against a "
        "clerk label on every one of the thirty-six; if the clerk and you part "
        "company on any subject here, those labels are not your classifications "
        "and the arm has no denominator anyone has checked. Twelve is a third "
        "of the arm, so one disagreement implies about three across it.",
        "",
        "The question on each is the taxonomy's own: **is this a class-level "
        "mechanism, naming no issuer, no instrument and no dated episode?**",
        "",
        f"## Drawn arm: {len(picked)} of the {len(_subjects(labelled)[0])}, labels withheld",
        "",
    ]
    for i, l in enumerate(picked, start=1):
        p = l.proposal
        out += [
            f"### {i}. `{l.subject_id}`",
            "",
            f"- **event_class**: {p.event_class}",
            f"- **corpus**: {p.corpus_id or 'n/a'}",
            f"- **event_definition**: {p.event_definition}",
            f"- **measured_on_intention**: {p.measured_on_intention}",
            f"- **mechanism_note**: {p.mechanism_note or 'n/a'}",
            "",
            "```",
            "operator_label (class_level / not_class_level):",
            "reason:",
            "```",
            "",
        ]
    out += [
        f"## Authored probes: all {len(probes)}, shown in full (§13 row 21b)",
        "",
        "Not withheld and not sampled. Row 21b asks whether each probe "
        "exercises the route it claims and whether these are the routes that "
        "matter, and both are answered by reading all six. This arm reports "
        "coverage and never a rate: a proportion over a chosen set estimates "
        "nothing, and doubling the set to twelve routes would halve any "
        "percentage whilst leaving the fence untouched.",
        "",
    ]
    for i, l in enumerate(sorted(probes, key=lambda x: x.subject_id), start=1):
        p = l.proposal
        out += [
            f"### {i}. `{l.subject_id}`: {l.probe_route}",
            "",
            f"- **event_definition**: {p.event_definition}",
            f"- **measured_on_intention**: {p.measured_on_intention}",
            f"- **clerk label**: "
            f"{'class_level' if l.is_class_level else 'not_class_level'}",
            "",
            "```",
            "route exercised as claimed (yes / no):",
            "route belongs in the set (yes / no):",
            "reason:",
            "```",
            "",
        ]
    out += [
        "## What ratifying this does and does not do",
        "",
        "Ratification makes the labels the operator's. It does **not** close "
        "row 21a, which is blocked on the design segment: the tolerance the "
        "rate must be known to is set by how much funnel depth §7.1 can lose "
        "before it loses power, and §7.1 has not run. It does **not** turn row "
        "21b's coverage into a rate; only a drawn episode-level sample could.",
        "",
        "The reading it would ratify is an **upper bound**, not a rate: 0 "
        "events in 36 trials, 95% upper bound approximately 8.3% by the rule "
        "of three. Zero events does not estimate zero.",
        "",
    ]
    return "\n".join(out) + "\n"


def reveal(
    labelled: List[LabelledProposal],
    seed: int,
    operator_labels: Dict[str, bool],
    n: int = DRAW_N,
) -> "Agreement":
    """Compare the operator's labels against the clerk's.  Counts, not a rate."""

    picked = draw(labelled, seed, n)
    ids = [l.subject_id for l in picked]
    missing = [i for i in ids if i not in operator_labels]
    if missing:
        raise RatificationRefused(
            "no operator label for: " + ", ".join(missing) + ". A subject left "
            "blank is not agreement and is not disagreement, and scoring the "
            "rest as though the draw were smaller would change the denominator "
            "the refutation rule is stated against."
        )
    disagreements = [
        (l.subject_id, l.is_class_level, operator_labels[l.subject_id])
        for l in picked
        if l.is_class_level != operator_labels[l.subject_id]
    ]
    return Agreement(
        n_drawn_arm=len(_subjects(labelled)[0]),
        n_examined=len(picked),
        disagreements=disagreements,
        digest=_digest(labelled, seed, n),
    )


@dataclass
class Agreement:
    """The result, reported as counts with their own denominator."""

    n_drawn_arm: int
    n_examined: int
    disagreements: List[Tuple[str, bool, bool]]
    digest: str

    @property
    def agreed(self) -> int:
        return self.n_examined - len(self.disagreements)

    @property
    def refutes(self) -> bool:
        """One is enough.  The rule was stated before the draw was taken."""

        return bool(self.disagreements)

    def render(self) -> str:
        lines = [
            "Ratification reveal (§13 rows 21a and 21b)",
            f"  draw digest                  : {self.digest}",
            f"  examined                     : {self.n_examined} of "
            f"{self.n_drawn_arm} drawn-arm subjects",
            f"  operator agrees with clerk   : {self.agreed} of {self.n_examined}",
            f"  disagreements                : {len(self.disagreements)}",
        ]
        for sid, clerk, op in self.disagreements:
            lines.append(
                f"    {sid}: clerk said "
                f"{'class_level' if clerk else 'not_class_level'}, operator said "
                f"{'class_level' if op else 'not_class_level'}"
            )
        lines.append("")
        if self.refutes:
            implied = round(
                len(self.disagreements) * self.n_drawn_arm / self.n_examined
            )
            lines += [
                "  REFUTED. The clerk's labels are refuted FOR THE WHOLE DRAWN",
                "  ARM, not for the subjects disagreed on. The rule was stated in",
                "  the draw file before any label was revealed: one disagreement",
                f"  in {self.n_examined} refutes the arm.",
                "",
                "  §13 row 21a's reading rests on a clerk label for each of the",
                f"  {self.n_drawn_arm}, and {len(self.disagreements)} in "
                f"{self.n_examined} implies roughly {implied} across it. The",
                "  reading is withdrawn until the operator relabels the arm, and",
                "  no partial credit is taken for the subjects agreed on.",
            ]
        else:
            lines += [
                f"  NOT REFUTED on this draw: {self.agreed} of {self.n_examined}.",
                "",
                "  A count over a third of the arm, and not a rate. It does not",
                f"  make the labels the operator's for the other "
                f"{self.n_drawn_arm - self.n_examined}: it removes",
                "  one reason to doubt them and adds no reason to call them",
                "  ratified. Row 21a stays BLOCKED on the design segment either",
                "  way, the tolerance its rate must be known to being set by",
                "  §7.1, which has not run.",
            ]
        return "\n".join(lines)
