"""Orchestration: sweep, ingest fail-fast, screen, direct, register, admit.

The shape of one scan cycle, and the point at which each fence bites:

    corpus (readable partition only)
      -> sweep            agent emits mechanisms, never episodes
      -> intake           FAIL-FAST: first failed point ends the idea
      -> screen           §3.6.3, check 3 binding
      -> directive        §3.6.5 lookup; new_subscription logged and deferred
      -> registration     blocked on what only the operator may supply
      -> admission        segment arithmetic; agent drafts queue, never displace

Everything that dies writes a reason code and a rendered §8 summary before the
next idea starts.  The scanner's honest output is three lists: directives
admitted, drafts blocked on the operator, and a graveyard that is larger than
both and is the actual product.
"""

from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import summaries
from .codes import coverage
from .discovery import (
    AgentClient,
    ControlArmVerdict,
    Corpus,
    GridCell,
    ProposalCache,
    draw_control_mechanisms,
    sweep,
)
from .fences import FenceReport, QueryFence, assert_import_fence
from .ingest import IntakeContext, Mode, intake_runner
from .ledger import Ledger
from .records import (
    DEFAULT_FENCE,
    ClaimField,
    Directive,
    EntityFence,
    IntakeRecord,
    Origin,
    Partition,
    Proposal,
    Provenance,
    Refusal,
    ScoringMode,
    SegmentSpan,
)
from .screen import (
    RegistrationInputs,
    build_directive,
    register,
    screen_pointer,
)
from .segment import ReuseLedger, SegmentPolicy, counting_family_four


@dataclass
class ScanConfig:
    parameter_hash: str = "unfrozen"
    #: §7.2's audit fraction, **read from the registration and never defaulted
    #: here**.
    #:
    #: *Why ``None`` and not 0.10.* It was 0.10 as a default on this dataclass
    #: and 0.10 again as a default in ``ingest.py``, and the registration did
    #: not carry it at all, so two runs under one parameter hash could audit
    #: different fractions with the difference attributable to nothing. It is
    #: registered from 27 August 2026; leaving a default here would leave the
    #: silent path open beside the registered one, which is the defect and not
    #: a convenience.
    audit_fraction: Optional[float] = None
    #: The registered default exclusivity construction, settled in v1.14 as
    #: ``cross_market``: it costs no archive span, where ``disjoint_partition``
    #: would take span from an archive already down to nine to twelve
    #: evaluation months.  What it buys with that saving is an assumption --
    #: that mechanisms generalise across markets even though episodes do not --
    #: and the assumption is disclosed on every verdict and measured by §13
    #: row 24 rather than left implicit.
    default_scoring_mode: ScoringMode = ScoringMode.CROSS_MARKET
    #: Event classes declared discoverable, per §13 row 22.  Membership decides
    #: *whether* a class may be discovered; a class **absent from this mapping
    #: is refused** with ``scoring_mode_unsatisfiable``, whatever corpus raised
    #: it.  The value is advisory and unused for the construction.
    exclusivity: Dict[str, Optional[ScoringMode]] = field(default_factory=dict)
    #: corpus_id -> the exclusivity guarantee that corpus provides.  The
    #: construction is a property of where material was read, not of the class
    #: read from it: one class from an ASX corpus is cross_market and from an
    #: EDGAR corpus is pre_archive.
    corpus_modes: Dict[str, ScoringMode] = field(default_factory=dict)
    #: Security master plus regulatory lexicon.  §13 row 22 names the lists.
    entity_fence: EntityFence = DEFAULT_FENCE
    policy: SegmentPolicy = field(default_factory=SegmentPolicy)
    manual_capacity: int = 0
    default_span_days: int = 180
    default_n_min: int = 30
    span_start: date = date(2024, 1, 1)
    #: Supplied per directive by the operator.  Absent means the draft blocks,
    #: which is the expected steady state rather than an error.
    registration_inputs: Dict[str, RegistrationInputs] = field(default_factory=dict)
    control_arm_ratio: float = 0.25
    control_arm_seed: int = 20260826


@dataclass
class ScanResult:
    admitted: List[Directive] = field(default_factory=list)
    blocked_on_operator: List[Tuple[Directive, List[Refusal]]] = field(default_factory=list)
    queued: List[Directive] = field(default_factory=list)
    abandoned: List[Tuple[str, Refusal]] = field(default_factory=list)
    fence_report: Optional[FenceReport] = None
    reuse: Optional[ReuseLedger] = None
    proposed: int = 0
    registered: int = 0
    promoted: int = 0
    #: Per family, and NEVER pooling the two arms. `{corpus_id: {...}}` for the
    #: agent arm and one `control_arm` entry beside it, because §13 row 20's
    #: whole purpose is a comparison, and a table that adds the two together
    #: destroys the only instrument that can refute the discovery layer.
    per_family: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def render(self, ledger: Ledger) -> str:
        blocks: List[str] = ["Scan cycle", ""]
        blocks.append(
            "\n".join(
                [
                    "Funnel",
                    f"  proposals raised             : {self.proposed}",
                    f"  abandoned at ingestion       : {len(self.abandoned)}",
                    f"  drafts blocked on operator   : {len(self.blocked_on_operator)}",
                    f"  queued behind capacity       : {len(self.queued)}",
                    f"  directives admitted          : {len(self.admitted)}",
                ]
            )
        )
        blocks.append("")
        if self.per_family:
            blocks.append("Per family, agent arm and control arm NEVER pooled")
            head = f"  {'family':<26}{'raised':>8}{'refused':>9}{'drafts':>8}{'admitted':>10}"
            blocks.append(head)
            for name in sorted(self.per_family):
                row = self.per_family[name]
                blocks.append(
                    f"  {name:<26}{row.get('raised', 0):>8}"
                    f"{row.get('refused', 0):>9}{row.get('blocked', 0):>8}"
                    f"{row.get('admitted', 0):>10}"
                )
            blocks.append(
                "  The control arm is sized on the agent arm at the registered"
            )
            blocks.append(
                "  ratio and drawn from the registered seed. It is a row here"
            )
            blocks.append(
                "  and never a column: pooling the arms would destroy the only"
            )
            blocks.append("  instrument that can refute the discovery layer.")
            blocks.append("")
        if self.fence_report:
            blocks.append(self.fence_report.render())
            blocks.append("")
        if self.reuse:
            blocks.append(self.reuse.render())
            blocks.append("")
        blocks.append(
            counting_family_four(self.proposed, self.registered, self.promoted)
        )
        blocks.append("")
        dist = ledger.code_distribution()
        if dist:
            blocks.append("Refusals by reason code")
            for code, n in dist:
                blocks.append(f"  {n:>4}  {code}")
            blocks.append("")
        declined = ledger.declined_feed_distribution()
        if declined:
            blocks.append("Declined-directive log, by feed named (§3.6.5)")
            for feed, n in declined:
                blocks.append(f"  {n:>4}  {feed}")
            blocks.append(
                "  Reported at freeze beside the roster decision: a persistent"
            )
            blocks.append(
                "  mismatch between ideas raised and streams held is evidence"
            )
            blocks.append("  the roster is wrong, not that §0.6 should be bypassed.")
            blocks.append("")
        blocks.append(coverage(ledger.emitted_codes()).render())
        return "\n".join(blocks)


def _claims_for(p: Proposal) -> Dict[str, Optional[str]]:
    """Provenance tags on the populated claim fields of a pointer record.

    A pointer's ``claimed_effect``, ``claimed_horizon_sessions``,
    ``cost_treatment`` and ``replication_status`` are empty by definition and
    those omissions are not defects.  What must carry a tag is the source
    reference the mechanism was read from.
    """

    return {"source_ref": Provenance.VERIFIED_PRIMARY.value if p.source_ref else None}


def scan(
    client: AgentClient,
    corpora: Sequence[Corpus],
    grid: Sequence[GridCell],
    config: ScanConfig,
    ledger: Ledger,
    fence: Optional[QueryFence] = None,
    source_resolver: Optional[Callable[[str], bool]] = None,
    now: Optional[datetime] = None,
    after_corpus: Optional[Callable[[int, int], None]] = None,
) -> ScanResult:
    now = now or datetime.now(timezone.utc)
    fence = fence or QueryFence()
    cache = ProposalCache()
    resolve = source_resolver or (lambda ref: bool(ref))
    if config.audit_fraction is None:
        raise ValueError(
            "ScanConfig.audit_fraction is unset. §7.2 calls it a pre-registered "
            "audit fraction and every attribution statistic computes on the "
            "audit sample exclusively, so a sweep that picked its own would "
            "make those statistics unattributable to any registration. Read it "
            "from Registration.audit_fraction."
        )
    runner = intake_runner(config.parameter_hash, config.audit_fraction)
    reuse = ReuseLedger(policy=config.policy)
    result = ScanResult(reuse=reuse)

    report = FenceReport(scoring_mode=config.default_scoring_mode.value)
    try:
        assert_import_fence("fntn.scanner.discovery")
        report.import_fence_clean = True
    except Exception as exc:  # pragma: no cover - fence failure is fatal
        report.import_fence_clean = False
        report.notes.append(str(exc))

    # -- gather proposals: agent arm, then the control arm ------------------
    proposals: List[Tuple[Proposal, Dict[str, object]]] = []
    off_schema: List[Tuple[str, int, str]] = []
    not_a_list: List[Tuple[str, str, int]] = []
    for index, corpus in enumerate(corpora):
        sweep_result = sweep(client, corpus, fence, cache, now=now)
        for p in sweep_result.proposals:
            proposals.append((p, {}))
        for element_index, got in sweep_result.off_schema:
            off_schema.append((corpus.corpus_id, element_index, got))
        if sweep_result.payload_not_a_list is not None:
            not_a_list.append((corpus.corpus_id, *sweep_result.payload_not_a_list))
        # The cost guard hooks HERE and not around three separate scans.
        # `control_count` is `round(len(all proposals) * ratio)` drawn once from
        # the registered seed; three scans would draw three arms from the same
        # seed over three smaller populations, which is not the construction
        # §13 row 20 registers. A guard that changed the control arm to measure
        # the cost of the treatment arm would be paid for in the only
        # instrument this layer has.
        if after_corpus is not None:
            after_corpus(index, len(corpora))

    # A sweep with no control arm is a sweep whose selection effect cannot be
    # measured, which makes the discovery layer unfalsifiable.  A configured
    # zero is refused rather than quietly floored: silently substituting a
    # working value for a broken one is the fallback-into-a-default this
    # architecture declines everywhere else.
    if config.control_arm_ratio <= 0:
        raise ValueError(
            "control_arm_ratio must exceed zero; a discovery layer with no "
            "random-mechanism control arm has no instrument that can refute it "
            "(§3.7.5), and running one is worse than running none because it "
            "produces directives nothing can attribute"
        )
    # **Sized on proposals and NOT on off-schema elements**, and the exclusion
    # is a decision rather than an oversight. The control arm exists to say
    # whether the agent located anything a random draw over the grid would not
    # have; an element that never became a mechanism is not something located,
    # and drawing a control mechanism to match it would inflate the control arm
    # against a treatment arm that did not grow.
    control_count = (
        max(1, round(len(proposals) * config.control_arm_ratio)) if proposals else 0
    )
    control_corpus = corpora[0].corpus_id if corpora else ""
    for p in draw_control_mechanisms(
        grid, control_count, config.control_arm_seed, now=now,
        corpus_id=control_corpus,
    ):
        proposals.append((p, {}))

    # **Off-schema elements are counted into the denominator.** The clerk
    # emitted them, so leaving them out would make the funnel report a
    # narrower search than the one that was paid for, and rule 5 says counting
    # is mechanical because intent flatters the denominator.
    result.proposed = len(proposals) + len(off_schema) + len(not_a_list)
    _payload_rows: List[str] = []
    for corpus_id, got, length in not_a_list:
        subject_id = f"prop-notalist-{corpus_id}"
        refusal = summaries.render(
            "agent_payload_not_a_list",
            subject_id,
            {"corpus_id": corpus_id, "got": got, "length": length,
             "failed_field": "proposals"},
        )
        ledger.write_refusals([refusal])
        result.abandoned.append((subject_id, refusal))
        _payload_rows.append(corpus_id)
    for corpus_id, element_index, got in off_schema:
        subject_id = f"prop-offschema-{corpus_id}-{element_index}"
        refusal = summaries.render(
            "agent_payload_off_schema",
            subject_id,
            {"index": element_index, "got": got, "corpus_id": corpus_id,
             "failed_field": "the element itself"},
        )
        ledger.write_refusals([refusal])
        result.abandoned.append((subject_id, refusal))
        _payload_rows.append(corpus_id)

    # Per-family counting, in memory rather than read back out of the ledger.
    # A ledger accumulates runs; this is one run's funnel, and reading it back
    # would silently pool this sweep with every earlier one under the same
    # parameter hash.
    _BUCKET = {
        "abandoned_at_ingestion": "refused",
        "refused_at_screen": "refused",
        "directive_deferred": "refused",
        "blocked_on_operator": "blocked",
        "queued": "queued",
        "admitted": "admitted",
    }

    def _family_of(p: Proposal) -> str:
        # **The control arm is its own row and never a corpus.** It is drawn
        # from the grid and carries the first corpus's id by construction, so
        # keying it on that id would file random draws under a family that did
        # not produce them and pool the two arms in the only table that exists
        # to keep them apart.
        return "control_arm" if p.origin is not Origin.AGENT else (p.corpus_id or "(none)")

    def terminal(subject_id: str, p: Proposal, outcome_name: str) -> None:
        ledger.write_proposal(subject_id, p, outcome_name)
        row = result.per_family.setdefault(
            _family_of(p),
            {"raised": 0, "refused": 0, "blocked": 0, "queued": 0, "admitted": 0},
        )
        row["raised"] += 1
        row[_BUCKET[outcome_name]] += 1

    open_pairs: Dict[Tuple[str, str], Dict[str, object]] = {}

    for proposal, raw_payload in proposals:
        subject_id = f"prop-{uuid.uuid4().hex[:10]}"

        ctx = IntakeContext(
            proposal=proposal,
            raw_payload=raw_payload,
            fence=fence,
            source_resolved=resolve(proposal.source_ref),
            open_pairs=open_pairs,
            exclusivity_available={
                k: (v or config.default_scoring_mode).value
                for k, v in config.exclusivity.items()
            },
            claim_provenance=_claims_for(proposal),
            entity_fence=config.entity_fence,
        )

        outcome = runner.run(subject_id, ctx)
        ledger.write_refusals(outcome.refusals)
        for r in outcome.refusals:
            if r.code == "proposal_names_entity":
                report.entity_refusals += 1
            elif r.code == "discovery_partition_violation":
                report.partition_refusals += 1
            elif r.code == "agent_overreached_schema":
                report.authority_refusals += 1
            elif r.code == "registered_at_unstampable":
                report.query_breaches += 1
            elif r.code == "security_master_unavailable":
                report.entity_refusals += 1
                if "no security master" not in " ".join(report.notes):
                    report.notes.append(
                        "no security master loaded: the entity fence's binding "
                        "layer could not run and every machine-origin proposal "
                        "refused to score"
                    )

        if not outcome.passed:
            terminal(subject_id, proposal, "abandoned_at_ingestion")
            assert outcome.first_refusal is not None
            result.abandoned.append((subject_id, outcome.first_refusal))
            continue  # <-- the rule: stop, and start the next idea.

        # -- intake record, screen ----------------------------------------
        record = IntakeRecord(
            intake_id=subject_id,
            origin=proposal.origin,
            event_definition=proposal.event_definition,
            event_class=proposal.event_class,
            measured_on=proposal.measured_on_intention,
            source_ref=proposal.source_ref,
            source_partition=proposal.source_partition,
            claims={
                "source_ref": ClaimField(
                    "source_ref", proposal.source_ref, Provenance.VERIFIED_PRIMARY
                )
            },
        )
        record.compute_evidence_tier()

        screened = screen_pointer(record)
        ledger.write_refusals(screened.refusals)
        if not screened.passed:
            terminal(subject_id, proposal, "refused_at_screen")
            result.abandoned.append((subject_id, screened.refusals[-1]))
            continue

        # -- directive ----------------------------------------------------
        scoring_mode = config.corpus_modes.get(
            proposal.corpus_id,
            config.exclusivity.get(record.event_class) or config.default_scoring_mode,
        )
        report.scoring_modes[scoring_mode.value] = (
            report.scoring_modes.get(scoring_mode.value, 0) + 1
        )
        span = SegmentSpan(
            start=config.span_start,
            end=date.fromordinal(config.span_start.toordinal() + config.default_span_days),
            population_key=record.measured_on,
        )
        draft = build_directive(
            record,
            directive_id=f"dir-{subject_id[5:]}",
            span=span,
            n_min=config.default_n_min,
            scoring_mode=scoring_mode,
            manual_capacity_remaining=config.manual_capacity,
        )
        ledger.write_refusals(draft.refusals)
        if draft.declined_feed:
            ledger.write_declined_feed(
                subject_id, draft.declined_feed, draft.refusals[0].code
            )
        if draft.directive is None:
            terminal(subject_id, proposal, "directive_deferred")
            result.abandoned.append((subject_id, draft.refusals[0]))
            continue

        directive = draft.directive
        open_pairs[(record.event_class, record.measured_on)] = {
            "directive_id": directive.directive_id,
            "registered_at": now.isoformat(),
        }

        # -- registration --------------------------------------------------
        inputs = config.registration_inputs.get(
            directive.directive_id, RegistrationInputs()
        )
        blocking = register(directive, inputs, config.policy.delta_min_floor, now)
        ledger.write_refusals(blocking)
        if blocking:
            terminal(subject_id, proposal, "blocked_on_operator")
            ledger.write_directive(directive, "blocked_on_operator")
            result.blocked_on_operator.append((directive, blocking))
            continue

        fence.register_population(
            f"{record.event_class}|{record.measured_on}", now
        )
        result.registered += 1

        # -- admission -----------------------------------------------------
        refusal = reuse.admit(directive)
        if refusal is not None:
            ledger.write_refusal(refusal)
            queued = reuse.enqueue(directive)
            ledger.write_refusal(queued)
            terminal(subject_id, proposal, "queued")
            ledger.write_directive(directive, "queued")
            result.queued.append(directive)
            continue

        terminal(subject_id, proposal, "admitted")
        ledger.write_directive(directive, "open")
        result.admitted.append(directive)

    for corpus_id in _payload_rows:
        row = result.per_family.setdefault(
            corpus_id,
            {"raised": 0, "refused": 0, "blocked": 0, "queued": 0, "admitted": 0},
        )
        row["raised"] += 1
        row["refused"] += 1

    ledger.write_query_log(fence.log)
    report.query_log_entries = len(fence.log)
    result.fence_report = report
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:  # pragma: no cover - CLI
    parser = argparse.ArgumentParser(
        description=(
            "From Narrative to Null -- agent discovery scanner. Locates "
            "mechanisms, ingests them fail-fast, and produces directives at "
            "zero capital. Produces no trading signal and cannot."
        )
    )
    parser.add_argument("--ledger", default=":memory:")
    parser.add_argument("--parameter-hash", default="unfrozen")
    parser.add_argument("--theta", type=float, default=0.25)
    parser.add_argument("--delta-min-floor", type=float, default=25.0)
    parser.add_argument("--segment-sessions", type=int, default=252)
    parser.add_argument("--calibration-reserve", type=int, default=126)
    args = parser.parse_args(argv)
    print(
        "This entry point requires an AgentClient and a readable corpus to be "
        "wired in from fntn/. See tests/test_scanner.py for a complete "
        "end-to-end example against a stub client."
    )
    print(
        f"policy: theta={args.theta} delta_min_floor={args.delta_min_floor} "
        f"segment={args.segment_sessions} reserve={args.calibration_reserve}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
