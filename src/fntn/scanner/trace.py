"""The specification trace harness for the discovery layer.

§9.4 applied to §3.7's two ingestion surfaces.  It is a *specification test
instrument*, not a production run, and the three properties that make it one are
enforced here rather than left to the operator's care:

* **It runs interactive always.**  Batch mode terminates at the first hard kill
  and therefore hides every downstream defect, so the trace runs FULL_PANEL on
  every subject regardless of the audit fraction.  The production runner's
  fail-fast behaviour is what is being *tested*, and a test that stops where the
  thing under test stops sees nothing.
* **Its output is a coverage report, not verdicts.**  Reason codes emitted
  against reason codes defined; abort position against ordering length; fields
  populated against fields defined.
* **Nothing it produces is evidentiary.**  Every record is stamped
  ``NON_EVIDENTIARY``, the harness refuses to register or admit a directive, and
  it writes to a ledger whose parameter hash says so on every row.  A trace that
  could quietly become an observation is a hole in the instrument being relied
  upon, which is the reason Gate 0's separation assertion extends to manual
  injections in the first place.

**What the trace can measure, and it is not nothing.** §13 row 21, the entity
fence's false-positive rate against hand labels, and §13 row 23, the
abort-position distribution.  Both are facts about the machinery rather than
about the market; therefore neither requires the archive, and neither consumes
the first sweep whose kill criterion is not yet registered.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .codes import INTAKE_ORDER, coverage
from .ingest import IntakeContext, Mode, intake_runner
from .ledger import Ledger
from .records import (
    DEFAULT_FENCE,
    EntityFence,
    Origin,
    Partition,
    Proposal,
    Provenance,
    Refusal,
    entity_mentions,
)

#: Stamped on every row the harness writes.  Chosen to be conspicuous in a
#: ledger query rather than tidy.
NON_EVIDENTIARY = "TRACE-NON-EVIDENTIARY"


class EvidentiaryUseRefused(RuntimeError):
    pass


@dataclass
class LabelledProposal:
    """A proposal with an independent label, for the fence audit.

    ``is_class_level`` is the label: True where a labeller blind to the fence's
    verdict judges the proposal genuinely class-level.  The fence's verdict is
    then compared against it.

    **The two arms are not the same kind of thing, and the audit does not treat
    them as one.**  The class-level arm is *drawn*: it is what the discovery
    agents actually swept, so the share of it the fence refuses is a rate.  The
    other arm is *authored*: each subject is a probe written to exercise one
    named route into the fence, so what it yields is coverage of those routes
    and never a rate.  ``probe_route`` carries the route a probe exercises, and
    it is the reason the arm can be reported at all: a probe set with no route
    names is a denominator with nothing behind it.
    """

    proposal: Proposal
    is_class_level: bool
    labeller: str = "operator"
    #: The subject's own identifier in the labelled set, so an open route can be
    #: named in the report rather than described.
    subject_id: str = ""
    #: For an authored probe, the route into the fence it exercises.  Empty on a
    #: drawn class-level subject, which probes nothing in particular.
    probe_route: str = ""


def load_labelled(
    path: str, partition: Partition = Partition.EXTERNAL
) -> List[LabelledProposal]:
    """Read the committed labelled set.

    The labels live in the repository as data rather than in whatever shell
    invoked the harness. The 26 August reading was taken against six plants
    defined inline in a heredoc that was never committed: the figure it produced
    could not be reproduced, and a fence error rate that cannot be reproduced is
    an assertion about a fence rather than a measurement of one.
    """

    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    out: List[LabelledProposal] = []
    for row in doc["labelled"]:
        raw = row["proposal"]
        out.append(
            LabelledProposal(
                proposal=Proposal(
                    event_definition=raw["event_definition"],
                    measured_on_intention=raw["measured_on_intention"],
                    event_class=raw["event_class"],
                    source_ref=raw["source_ref"],
                    source_partition=partition,
                    corpus_id=row.get("corpus_id", ""),
                    mechanism_note=raw.get("mechanism_note", ""),
                    origin=Origin.AGENT,
                ),
                is_class_level=bool(row["is_class_level"]),
                labeller=row.get("labeller", "unrecorded"),
                subject_id=row.get("id", ""),
                probe_route=row.get("probe_route", ""),
            )
        )
    return out


@dataclass
class FenceAudit:
    """§13 row 21.  One arm is a rate; the other is coverage, and never a rate.

    **The class-level arm is drawn, so it yields a rate.**  Its subjects are what
    the discovery agents actually swept, and the share of them the fence refuses
    is an estimate of the share of real clean proposals it would refuse.  It is
    divided by its own n and by nothing else.

    **The probe arm is authored, so it yields coverage.**  Its subjects are
    written, one per route into the fence, to establish that each route is
    closed: a designator, a bare ticker in capitals, a bare ticker in title
    case, an exchange-prefixed identifier, an ISIN, a one-word name equal to its
    own ticker.  A chosen set has no sampling frame, so a proportion over it
    estimates nothing.  Printing "1 of 6 (17%)" invites the reader to take 17%
    as the fence's error rate on real episode-level material, which it is not
    and cannot be: change the probe set from six routes to twelve and the
    percentage halves whilst the fence is untouched.  **The probe arm therefore
    reports which routes are closed and which are open, by name, and prints no
    percentage at all.**

    An earlier version reported both arms as rates over the 42-subject union.
    Fixing the denominator left the frame wrong, which is the more expensive
    half: a number with the right denominator and the wrong meaning still
    travels, and it travels as a rate.
    """

    #: Total labelled subjects.  Reported, and used for the 200-subject
    #: PROVISIONAL note only.  It is never a denominator of a rate.
    n: int = 0
    #: Drawn class-level subjects: the population a false positive can come
    #: from, and the only denominator the false-positive rate has.
    n_class_level: int = 0
    #: Authored probes.  A count of routes exercised, not a sample size.
    n_probes: int = 0
    #: Fence refused a proposal the label calls class-level.  The cost of
    #: bluntness, paid in re-raises.  A rate, over ``n_class_level``.
    false_positives: int = 0
    #: Probes the fence refused: routes shown closed.
    routes_closed: int = 0
    #: Probes the fence passed, as ``(route, subject id)``: routes left open.
    #: Named rather than counted, because an open route is a specific hole and
    #: the name is what makes it actionable.
    routes_open: List[Tuple[str, str]] = field(default_factory=list)
    examples: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def false_positive_rate(self) -> Optional[float]:
        """``None`` where the arm is empty, never zero.

        An empty arm is a refusal to score under rule 3, not a clean fence: a
        fence measured against no clean proposals has not been shown to pass
        one.
        """

        if not self.n_class_level:
            return None
        return self.false_positives / self.n_class_level

    def render(self) -> str:
        if not self.n:
            return "Entity-fence audit (§13 row 21): no labelled proposals"
        lines = [
            "Entity-fence audit (§13 row 21)",
            f"  labelled subjects               : {self.n} "
            f"({self.n_class_level} drawn class-level, "
            f"{self.n_probes} authored probes)",
            "",
            f"  drawn class-level              : {self.n_class_level}",
        ]
        if self.n_class_level:
            lines.append(
                f"    false positives (clean refused): {self.false_positives} "
                f"of {self.n_class_level} "
                f"({self.false_positives / self.n_class_level:.0%})"
            )
            lines.append(
                "    A rate: this arm was drawn, and is divided by its own n."
            )
        else:
            lines.append(
                "    not scored, no subjects in this arm"
            )

        lines.append("")
        lines.append(f"  authored probes                : {self.n_probes}")
        if self.n_probes:
            lines.append(
                f"    routes closed                : "
                f"{self.routes_closed} of {self.n_probes}"
            )
            if self.routes_open:
                label = (
                    "route left open              : "
                    if len(self.routes_open) == 1
                    else "routes left open             : "
                )
                first, *rest = self.routes_open
                lines.append(f"    {label}{first[0]} ({first[1]})")
                for route, subject in rest:
                    lines.append(f"    {' ' * len(label)}{route} ({subject})")
            else:
                lines.append("    routes left open             : none")
            lines.append(
                "    NOT a rate: probes are chosen, not sampled."
            )
        else:
            lines.append("    not scored, no subjects in this arm")

        lines.append("")
        if self.n < 200:
            lines.append(
                f"  PROVISIONAL: row 21 specifies 200 hand-labelled proposals; "
                f"this is {self.n}. Reported as a reading, not as the calibration."
            )
        for kind, text in self.examples[:6]:
            lines.append(f"    {kind}: {text[:110]}")
        return "\n".join(lines)


@dataclass
class TraceReport:
    subjects: int = 0
    passed: int = 0
    abort_positions: Counter = field(default_factory=Counter)
    codes: Counter = field(default_factory=Counter)
    fence_audit: FenceAudit = field(default_factory=FenceAudit)
    notes: List[str] = field(default_factory=list)

    def render(self, ledger: Ledger) -> str:
        blocks = [
            "SPECIFICATION TRACE (§9.4 applied to §3.7)",
            f"stamp: {NON_EVIDENTIARY}. No row here may be counted as an "
            "observation, and the harness refuses to register or admit.",
            "",
            "Intake surface",
            f"  subjects run (full panel)    : {self.subjects}",
            f"  cleared every point          : {self.passed}",
            f"  refused at least one point   : {self.subjects - self.passed}",
            "",
        ]

        blocks.append("Abort-position distribution (§13 row 23)")
        if self.abort_positions:
            for pos in range(1, len(INTAKE_ORDER) + 1):
                n = self.abort_positions.get(pos, 0)
                bar = "#" * n
                name = INTAKE_ORDER[pos - 1]
                blocks.append(f"  {pos:>2}. {name:<32} {n:>3} {bar}")
            deepest = max(self.abort_positions)
            blocks.append(
                f"  deepest position reached by a failure: {deepest} of "
                f"{len(INTAKE_ORDER)}"
            )
            if deepest < len(INTAKE_ORDER):
                blocks.append(
                    "  Points below the deepest failure were reached and passed, "
                    "not skipped: the panel runs in full."
                )
        else:
            blocks.append("  no failures recorded")
        blocks.append("")

        blocks.append("Every refusal emitted, not only first failures")
        if self.codes:
            for code, n in self.codes.most_common():
                pos = (
                    str(INTAKE_ORDER.index(code) + 1)
                    if code in INTAKE_ORDER
                    else "n/a"
                )
                blocks.append(f"  {n:>4}  pos {pos:<4} {code}")
            blocks.append(
                "  The distribution above counts first failures only. A point "
                "that fires behind an earlier one is invisible there and "
                "appears here, so the two are reported together."
            )
        else:
            blocks.append("  none")
        blocks.append("")

        blocks.append(self.fence_audit.render())
        blocks.append("")
        blocks.append(coverage(ledger.emitted_codes()).render())
        if self.notes:
            blocks.append("")
            blocks.append("Trace findings")
            blocks.extend(f"  - {n}" for n in self.notes)
        return "\n".join(blocks)


class TraceHarness:
    """Runs proposals through the real intake path, evidentially inert."""

    def __init__(
        self,
        exclusivity_available: Dict[str, str],
        entity_fence: Optional[EntityFence] = None,
    ) -> None:
        self.ledger = Ledger(parameter_hash=NON_EVIDENTIARY)
        self.runner = intake_runner(parameter_hash=NON_EVIDENTIARY)
        self.exclusivity_available = exclusivity_available
        self.entity_fence = entity_fence or DEFAULT_FENCE
        self.report = TraceReport()

    # -- the bar on evidentiary use ---------------------------------------

    def register(self, *_args, **_kwargs):
        raise EvidentiaryUseRefused(
            "the trace harness may not register a directive: its subjects were "
            "run without a registered kill criterion, so nothing it touched can "
            "be attributed (§13 rows 19-20)"
        )

    admit = register

    # -- the run -----------------------------------------------------------

    def run(
        self,
        labelled: Sequence[LabelledProposal],
        fence,
        source_resolver=None,
    ) -> TraceReport:
        resolve = source_resolver or (lambda ref: bool(ref))
        audit = self.report.fence_audit

        for i, lp in enumerate(labelled):
            subject_id = f"trace-{i:04d}"
            p = lp.proposal
            ctx = IntakeContext(
                proposal=p,
                raw_payload={},
                fence=fence,
                source_resolved=resolve(p.source_ref),
                open_pairs={},
                exclusivity_available=self.exclusivity_available,
                claim_provenance={
                    "source_ref": Provenance.VERIFIED_PRIMARY.value if p.source_ref else None
                },
                entity_fence=self.entity_fence,
            )
            outcome = self.runner.run(subject_id, ctx, mode=Mode.FULL_PANEL)
            self.ledger.write_refusals(outcome.refusals)
            self.ledger.write_proposal(
                subject_id, p, "traced_pass" if outcome.passed else "traced_refused"
            )

            self.report.subjects += 1
            if outcome.passed:
                self.report.passed += 1
            if outcome.failed_at_position:
                self.report.abort_positions[outcome.failed_at_position] += 1
            for r in outcome.refusals:
                self.report.codes[r.code] += 1

            # -- the fence audit, §13 row 21 -------------------------------
            fence_refused = any(
                r.code == "proposal_names_entity" for r in outcome.refusals
            )
            audit.n += 1
            if lp.is_class_level:
                audit.n_class_level += 1
                if fence_refused:
                    audit.false_positives += 1
                    audit.examples.append(
                        (
                            "false positive",
                            f"{entity_mentions(p.fenced_text(), self.entity_fence)} "
                            f"in: {p.event_definition}",
                        )
                    )
            else:
                audit.n_probes += 1
                if fence_refused:
                    audit.routes_closed += 1
                else:
                    audit.routes_open.append(
                        (lp.probe_route or "route unnamed", lp.subject_id or subject_id)
                    )

        return self.report

    def note(self, text: str) -> None:
        self.report.notes.append(text)

    def close(self) -> None:
        self.ledger.close()
