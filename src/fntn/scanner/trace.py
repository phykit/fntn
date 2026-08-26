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

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .codes import INTAKE_ORDER, coverage
from .ingest import IntakeContext, Mode, intake_runner
from .ledger import Ledger
from .records import (
    DEFAULT_FENCE,
    EntityFence,
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
    """A proposal with an independent hand label, for the fence audit.

    ``is_class_level`` is the label: True where a human (or a labeller blind to
    the fence's verdict) judges the proposal genuinely class-level.  The fence's
    verdict is then compared against it, and the disagreements are the two error
    rates §13 row 21 asks for.
    """

    proposal: Proposal
    is_class_level: bool
    labeller: str = "operator"


@dataclass
class FenceAudit:
    """§13 row 21.  Reported with its n, always."""

    n: int = 0
    #: Fence refused a proposal the label calls class-level.  The cost of
    #: bluntness, paid in re-raises.
    false_positives: int = 0
    #: Fence passed a proposal the label calls episode-level.  The cost that
    #: matters, paid in the exclusivity guarantee.
    false_negatives: int = 0
    examples: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def false_positive_rate(self) -> Optional[float]:
        return self.false_positives / self.n if self.n else None

    def render(self) -> str:
        if not self.n:
            return "Entity-fence audit (§13 row 21): no labelled proposals"
        lines = [
            "Entity-fence audit (§13 row 21)",
            f"  labelled proposals           : {self.n}",
            f"  false positives (clean refused) : {self.false_positives} "
            f"({self.false_positives / self.n:.0%})",
            f"  false negatives (episode passed): {self.false_negatives} "
            f"({self.false_negatives / self.n:.0%})",
        ]
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
            if fence_refused and lp.is_class_level:
                audit.false_positives += 1
                audit.examples.append(
                    (
                        "false positive",
                        f"{entity_mentions(p.fenced_text(), self.entity_fence)} "
                        f"in: {p.event_definition}",
                    )
                )
            elif not fence_refused and not lp.is_class_level:
                audit.false_negatives += 1
                audit.examples.append(("false negative", p.event_definition))

        return self.report

    def note(self, text: str) -> None:
        self.report.notes.append(text)

    def close(self) -> None:
        self.ledger.close()
