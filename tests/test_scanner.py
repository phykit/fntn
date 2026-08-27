"""Tests for the agent discovery scanner.

Two obligations, and the second is the one that matters:

1. Every fence refuses what it exists to refuse.
2. **Every defined reason code is emitted at least once.**  §9.4's finding was
   that the defects audits structurally cannot see are rules that are wrong
   because nothing ever reached them, and a code defined but never emitted is
   exactly that.  ``test_every_defined_code_is_emitted`` is therefore the
   headline test of this suite, not a completeness nicety.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

from pathlib import Path

import pytest

from fntn.scanner import codes, summaries
from fntn.scanner.discovery import (
    Corpus,
    GridCell,
    ProposalCache,
    SYSTEM_PROMPT,
    ControlArmVerdict,
    draw_control_mechanisms,
    sweep,
)
from fntn.scanner.fences import (
    ImportFenceBreach,
    QueryFence,
    QueryFenceBreach,
    QueryKind,
    assert_agent_authority,
    assert_import_fence,
)
from fntn.scanner.ingest import (
    IntakeContext,
    Mode,
    ObservationContext,
    intake_runner,
    observation_runner,
)
from fntn.scanner.budget import (
    BudgetDecision,
    BudgetReplayError,
    MeasuringBudget,
    ReplayedBudget,
    decisions_from_rows,
    decisions_to_rows,
)
from fntn.scanner.ledger import Ledger
from fntn.scanner.records import (
    Directive,
    EvidenceTier,
    Item,
    Origin,
    Partition,
    PreMortem,
    Proposal,
    Provenance,
    ScoringMode,
    SegmentSpan,
    StreamProvenance,
    StreamStatus,
    DEFAULT_FENCE,
    EntityFence,
    SEED_LEXICON,
    entity_mentions,
)
from fntn.scanner.run import ScanConfig, scan
from fntn.scanner.screen import (
    RegistrationInputs,
    build_directive,
    register,
    screen_pointer,
)
from fntn.scanner.segment import ReuseLedger, SegmentPolicy
from fntn.scanner.trace import FenceAudit, TraceHarness, load_labelled
from fntn.scanner.records import IntakeRecord, ClaimField, RULEBOOK_STOPWORDS

NOW = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Stub agent.
# ---------------------------------------------------------------------------


class StubClient:
    def __init__(self, payloads):
        self._payloads = list(payloads)
        self.calls = 0

    def complete(self, system, user, schema):
        self.calls += 1
        return self._payloads.pop(0) if self._payloads else {"proposals": []}


def clean_proposal(**overrides) -> Proposal:
    base = dict(
        event_definition=(
            "open-market acquisitions by two or more directors of one issuer "
            "settled within five sessions of each other"
        ),
        measured_on_intention="main market and growth market listings above the tradability floor",
        event_class="insider_dealing",
        source_ref="external://regulatory-register/sample",
        source_partition=Partition.EXTERNAL,
        origin=Origin.AGENT,
        raised_at=NOW,
    )
    base.update(overrides)
    return Proposal(**base)


def intake_ctx(proposal, **overrides) -> IntakeContext:
    base = dict(
        proposal=proposal,
        raw_payload={},
        fence=QueryFence(),
        source_resolved=True,
        open_pairs={},
        exclusivity_available={"insider_dealing": "cross_market", "buyback": "cross_market"},
        claim_provenance={"source_ref": Provenance.VERIFIED_PRIMARY.value},
        entity_fence=FENCE,
    )
    base.update(overrides)
    return IntakeContext(**base)


def run_intake(ctx, subject_id="s1", mode=Mode.FAIL_FAST, budget=None):
    return intake_runner(budget=budget).run(subject_id, ctx, mode=mode)


# ---------------------------------------------------------------------------
# The structural fence: mechanisms, never episodes.
# ---------------------------------------------------------------------------


#: A stand-in master. In production these are the security master and the
#: discovery markets' listing lists, named in §13 row 22. Names and tickers are
#: separate because the fence matches them by different rules.
MASTER = frozenset({"barclays", "vodafone", "acme"})
TICKERS = frozenset({"aapl", "vod", "bhp"})
FENCE = EntityFence(security_master=MASTER, tickers=TICKERS, lexicon=SEED_LEXICON)


@pytest.mark.parametrize(
    "text",
    [
        "purchases at Barclays PLC following results",
        "directors buying AAPL after a fall",
        "GB00B03MLX29 showed the effect",
        "acquisitions filed under LSE:VOD during the closed period",
        "the pattern observed at Vodafone Group PLC in March 2024",
    ],
)
def test_entity_fence_detects_episodes(text):
    assert entity_mentions(text, FENCE), f"fence missed an episode: {text}"


@pytest.mark.parametrize(
    "text",
    [
        # Regulatory vocabulary. The pattern-only fence refused all of these,
        # which is the defect the trace found and this repair removes.
        "notifications lodged with ASX under Listing Rule 12.9",
        "SEDI reports filed under NI 55-104 within five days",
        "managers' transactions notified under MAR Article 19(11)",
        "positions filed under UMIR 10.10 and published by CIRO",
        "reviews of the DAX and AEX families under the published rulebook",
        "guidance issued by ESMA, BaFin and the AFM",
        # Dates with no entity are not episodes: a mechanism may refer to a
        # regulatory calendar, and refusing that refuses the whole class.
        "the pattern seen in March 2024",
        "the Q3 2025 review cycle",
        "filings under the 2016 delegated regulation",
    ],
)
def test_entity_fence_passes_regulatory_vocabulary_and_bare_dates(text):
    assert entity_mentions(text, FENCE) == [], f"false positive on: {text}"


def test_entity_fence_passes_a_clean_mechanism():
    assert entity_mentions(clean_proposal().fenced_text(), FENCE) == []


def test_a_date_is_episodic_only_when_bound_to_an_entity():
    assert entity_mentions("effective in March 2024", FENCE) == []
    assert entity_mentions("Barclays PLC in March 2024", FENCE)


@pytest.mark.parametrize(
    "text",
    [
        # Title case and lower case are words, whatever the ticker table says.
        "a Vod filing lodged in the window",
        "purchases recorded as vod in the register",
        # Two characters is too short to carry the signal. The US master holds
        # T, IT, ON, FR and ARE as tickers; the corpus trace tripped on all of
        # them, and the length floor is what removes them.
        "the IT function of the issuer",
        "published in the FR under the rule",
    ],
)
def test_a_bare_ticker_matches_only_in_a_symbols_shape(text):
    """§13 row 21. The ticker set entered the fence unfiltered and refused
    ordinary English at 257 hits across the thirteen US corpus documents."""

    assert entity_mentions(text, FENCE) == [], f"false positive on: {text}"


@pytest.mark.parametrize(
    "text",
    [
        "directors buying AAPL after a fall",
        "positions in BHP disclosed late",
    ],
)
def test_an_all_capital_ticker_of_three_or_more_still_matches(text):
    assert entity_mentions(text, FENCE), f"fence missed a ticker: {text}"


def test_the_ticker_rule_takes_a_false_negative_and_names_it():
    """The cost of the length-and-case rule, asserted rather than described.

    A bare ticker in title case is invisible. Sixty-five US issuers have a
    one-word name identical to their ticker, so the *name* half must keep
    matching them or the rule would cost their names too; that is why the two
    sets are separate fields.
    """

    assert entity_mentions("purchases at Aapl in the window", FENCE) == []
    both = EntityFence(
        security_master=frozenset({"dole"}),
        tickers=frozenset({"dole"}),
        lexicon=SEED_LEXICON,
    )
    assert entity_mentions("purchases at Dole in the window", both)
    assert entity_mentions("purchases at DOLE in the window", both)


def test_the_committed_labelled_set_loads_and_carries_both_arms():
    """§13 row 21's denominator is in the tree, not in whatever shell ran it.

    The 26 August reading was measured against six plants defined inline in an
    uncommitted heredoc. The figure could not be reproduced from the repository,
    which makes it an assertion about the fence rather than a measurement of it.
    """

    labelled = load_labelled("docs/labelled_proposals.json")
    assert len(labelled) == 42
    assert sum(1 for l in labelled if l.is_class_level) == 36
    probes = [l for l in labelled if not l.is_class_level]
    assert len(probes) == 6
    # Every probe names the route it exercises. A probe set with no route names
    # is a denominator with nothing behind it, and the arm could not be reported
    # as coverage at all.
    assert all(l.probe_route and l.subject_id for l in probes)
    assert {l.subject_id for l in probes} == {f"plant-0{i}" for i in range(1, 7)}
    # Row 21 asks for hand labels. These are not, and the file says so.
    assert all(l.labeller == "model_clerk" for l in labelled)


def test_fence_audit_against_the_committed_set_and_the_real_us_master():
    """The §13 row 21 reading, locked so a fence change cannot move it quietly.

    Read against the real security master rather than a stand-in, because the
    defect this exercise found lived in the real master's ticker table and a
    six-name fixture would not have contained it.
    """

    m = SecurityMaster()
    m.load_sec_tickers("./master/us.json", market="US")
    harness = TraceHarness(
        exclusivity_available={"insider_dealing": "pre_archive",
                               "major_holdings_change": "pre_archive",
                               "buyback": "pre_archive",
                               "earnings_event": "pre_archive"},
        entity_fence=m.as_fence(),
    )
    report = harness.run(load_labelled("docs/labelled_proposals.json"), QueryFence())
    audit = report.fence_audit
    # The drawn arm is a rate. No clean class-level mechanism is refused; before
    # the ticker rule this was three of thirty-six, on "Note", "T" and "It".
    assert audit.n == 42
    assert audit.n_class_level == 36
    assert audit.false_positives == 0
    assert audit.false_positive_rate == 0.0
    # The probe arm is coverage. Five of the six routes are closed; the sixth is
    # the residual the ticker rule takes on knowingly, and it is named.
    assert audit.n_probes == 6
    assert audit.routes_closed == 5
    assert audit.routes_open == [("title-case bare ticker", "plant-03")]
    harness.close()


def test_the_probe_arm_reports_coverage_and_never_a_percentage():
    """§13 row 21, the frame rather than the denominator.

    The probes are authored, one per route into the fence, so they have no
    sampling frame and a proportion over them estimates nothing. "1 of 6 (17%)"
    reads as the fence's error rate on real episode-level material, which it is
    not: doubling the probe set to twelve routes halves the percentage whilst
    leaving the fence untouched. The arm therefore prints named routes and no
    percentage, and this test is what holds that.
    """

    audit = FenceAudit(
        n=10,
        n_class_level=4,
        n_probes=6,
        false_positives=1,
        routes_closed=4,
        routes_open=[("ISIN", "plant-05"), ("title-case bare ticker", "plant-03")],
    )
    text = audit.render()
    probe_arm = text.split("authored probes                :")[1]
    assert "%" not in probe_arm, probe_arm
    assert "4 of 6" in probe_arm
    assert "ISIN (plant-05)" in probe_arm
    assert "title-case bare ticker (plant-03)" in probe_arm
    assert "NOT a rate" in probe_arm
    # The drawn arm keeps its rate, over its own n and not over the union of 10.
    assert "1 of 4 (25%)" in text


def test_the_drawn_arm_divides_by_its_own_n():
    """The denominator, on a shape chosen to make the error visible.

    Nineteen drawn class-level subjects with one refusal reads 5% over its own
    arm and 4% over a 24-subject union. A rate divided by the wrong population
    is worse than no rate, because it is a number and it will be quoted.
    """

    audit = FenceAudit(n=24, n_class_level=19, n_probes=5, false_positives=1,
                       routes_closed=5)
    assert audit.false_positive_rate == pytest.approx(1 / 19)
    text = audit.render()
    assert "1 of 19" in text
    # Both arm sizes named in the output, not left to be inferred from the total.
    assert "19 drawn class-level" in text and "5 authored probes" in text
    assert "routes left open             : none" in text


def test_an_empty_arm_refuses_to_score_rather_than_reading_zero():
    """Rule 3 at the denominator, on both arms. A fence measured against no
    clean proposals has not been shown to pass one, and a fence against which
    no route was probed has not been shown to close one."""

    no_drawn = FenceAudit(n=6, n_class_level=0, n_probes=6, routes_closed=6)
    assert no_drawn.false_positive_rate is None
    assert "not scored, no subjects in this arm" in no_drawn.render()

    no_probes = FenceAudit(n=36, n_class_level=36, n_probes=0, false_positives=3)
    assert "not scored, no subjects in this arm" in no_probes.render()
    assert "of 0" not in no_probes.render()


def test_a_rulebook_heading_is_not_a_firm_however_the_designator_reads():
    """§13 row 21. The designator branch fired on Rule 16a-8's own heading.

    "Trust Holdings and Transactions" matches the legal-form grammar exactly as
    "Vodafone Group Holdings" does, and the pattern cannot tell them apart:
    Holdings is a designator in both. The leading token is what separates them,
    and it is separated by a registered stopword set rather than by a better
    pattern, because the set can be audited and a pattern cannot.
    """

    fence = EntityFence(
        security_master=MASTER,
        tickers=TICKERS,
        lexicon=SEED_LEXICON,
        rulebook_stopwords=RULEBOOK_STOPWORDS,
    )
    # The heading, as it appears in the corpus.
    assert entity_mentions("Trust Holdings and Transactions", fence) == []
    # "Joint and group filings" in Rule 16a-3: The Joint Corp is a listed US
    # issuer whose one-word name is an ordinary English word, so this one is
    # closed by a lexicon row rather than by the stopword set.
    assert entity_mentions("Joint and group filings must include", fence) == []


def test_a_genuine_designator_span_is_still_flagged():
    """The other half of the same rule, so the narrowing cannot go unnoticed.

    The span matcher is greedy, so a firm whose name merely contains a stopword
    leads on the word before it and is unaffected. Only a firm whose name
    *begins* with a rulebook noun loses this branch, and that cost is stated on
    RULEBOOK_STOPWORDS.
    """

    fence = EntityFence(
        security_master=MASTER,
        tickers=TICKERS,
        lexicon=SEED_LEXICON,
        rulebook_stopwords=RULEBOOK_STOPWORDS,
    )
    assert entity_mentions("Northern Trust Holdings raised its stake", fence)
    assert entity_mentions("purchases by Vodafone Group Holdings", fence)
    assert entity_mentions("a filing by Acme Inc in the window", fence)
    # The shape guard: a bare initial and a section number never lead a firm.
    assert entity_mentions("A Ltd", fence) == []
    assert entity_mentions("16a Holdings", fence) == []


def test_the_stopword_set_is_registered_so_it_reaches_the_hash():
    """A value that changes what the fence refuses must change the hash.

    Otherwise the fence's behaviour cannot be attributed to a registration, and
    a row added quietly to a module constant would silently widen what a sweep
    lets through with nothing on the record to show it.
    """

    from fntn.scanner.params import Registration

    a = Registration(rulebook_stopwords=["trust"])
    b = Registration(rulebook_stopwords=["trust", "beneficial"])
    assert a.hash() != b.hash()
    assert Registration().rulebook_stopwords == sorted(RULEBOOK_STOPWORDS)


def _corpus_documents():
    """The corpus as the sweep reads it: every file that is not a manifest.

    Globbed by exclusion rather than by extension. An earlier version of this
    test globbed `*.htm`, and when the corpus became extracted text it matched
    nothing and passed on an empty set, which is the way a corpus test fails
    silently: the assertions below are all negative, so zero documents satisfies
    every one of them.
    """

    docs = [p for p in sorted(Path("corpora/us").glob("*"))
            if p.is_file() and not p.name.startswith("_")]
    assert len(docs) == 13, f"expected the thirteen US documents, found {len(docs)}"
    return docs


def _corpus_hits():
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    m = SecurityMaster(lexicon=frozenset(reg.lexicon))
    m.load_sec_tickers("./master/us.json", market="US")
    fence = m.as_fence(stopwords=frozenset(reg.rulebook_stopwords))
    hits = []
    for doc in _corpus_documents():
        hits.extend(entity_mentions(
            doc.read_text(encoding="utf-8", errors="replace"), fence
        ))
    return hits


def test_the_corpus_no_longer_trips_the_designator_branch():
    """The reading this repair was raised against, locked against the corpus."""

    hits = set(_corpus_hits())
    assert "Trust Holdings" not in hits
    assert "Joint" not in hits


def test_the_corpus_produces_no_fence_hits_at_all():
    """§13 row 22's residual, locked.

    `API`, `BlackBerry` and `Opera` were page furniture rather than fence
    defects: an HTML comment and a user-agent sniffer in `<head>`, refused once
    per document on thirteen documents that name no company. Storing extracted
    text rather than HTML removed the constructs they lived in.

    This is a COUNT over the corpus, not a rate: it is what the fence refuses
    on this material, divided by nothing. §13 row 21's two arms are measured
    against the labelled set and are untouched by it.
    """

    assert _corpus_hits() == []


def test_no_security_master_refuses_to_score():
    """Patterns alone are not a fence, so the weaker half does not pass alone."""

    outcome = run_intake(intake_ctx(clean_proposal(), entity_fence=DEFAULT_FENCE))
    assert outcome.first_refusal.code == "security_master_unavailable"


def test_named_entity_proposal_dies_at_the_fence():
    p = clean_proposal(
        mechanism_note="as seen at Vodafone Group PLC in March 2024",
    )
    outcome = run_intake(intake_ctx(p))
    assert not outcome.passed
    assert outcome.first_refusal.code == "proposal_names_entity"
    # The fence runs before anything opens a document.
    assert outcome.failed_at_position <= 3


def test_fence_runs_before_retrieval():
    """A proposal breaching a fence must not have its source retrieved."""

    p = clean_proposal(mechanism_note="observed at Acme Corp")
    ctx = intake_ctx(p, source_resolved=False)
    outcome = run_intake(ctx)
    # Two failures are available; the fence must be the one that fires.
    assert outcome.first_refusal.code == "proposal_names_entity"
    assert "source_inaccessible" not in [r.code for r in outcome.refusals]


# ---------------------------------------------------------------------------
# The partition fence.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "partition", [Partition.DESIGN, Partition.CALIBRATION, Partition.EVALUATION]
)
def test_scored_partitions_are_unreadable(partition):
    p = clean_proposal(source_partition=partition)
    outcome = run_intake(intake_ctx(p))
    assert outcome.first_refusal.code == "discovery_partition_violation"


def test_corpus_refuses_construction_in_a_scored_partition():
    with pytest.raises(PermissionError):
        Corpus("c1", Partition.EVALUATION, ["doc"])


@pytest.mark.parametrize("partition", [Partition.DISCOVERY, Partition.EXTERNAL])
def test_readable_partitions_are_readable(partition):
    assert Corpus("c1", partition, ["doc"]).partition is partition


# ---------------------------------------------------------------------------
# The authority fence.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field", ["delta_min", "evidence_tier", "n_min", "merit", "severity", "stream", "verdict"]
)
def test_agent_may_not_populate_reserved_fields(field):
    assert assert_agent_authority({field: "something"}) == field


def test_reserved_field_kills_the_whole_proposal():
    ctx = intake_ctx(clean_proposal(), raw_payload={"delta_min": 40.0})
    outcome = run_intake(ctx)
    assert outcome.first_refusal.code == "agent_overreached_schema"
    assert "delta_min" in outcome.first_refusal.summary


def test_proposal_type_has_no_reserved_fields():
    """The strongest form of the fence: the field does not exist to be set."""

    for name in ("delta_min", "n_min", "evidence_tier", "merit", "priority", "stream"):
        assert not hasattr(clean_proposal(), name)


# ---------------------------------------------------------------------------
# The query fence.
# ---------------------------------------------------------------------------


def test_conditional_return_query_before_registration_is_refused_outright():
    fence = QueryFence()
    with pytest.raises(QueryFenceBreach):
        fence.guard(
            QueryKind.CONDITIONAL_RETURN, "insider_dealing|aim", "operator", "CAR by class"
        )


def test_class_level_queries_are_open():
    fence = QueryFence()
    fence.guard(QueryKind.CLASS_LEVEL, "insider_dealing|aim", "operator", "how many filings")
    assert len(fence.log) == 1


def test_contaminated_population_blocks_registration():
    fence = QueryFence()
    fence.record(
        QueryKind.CONDITIONAL_RETURN,
        "insider_dealing|main market and growth market listings above the tradability floor",
        "five-day CAR conditioned on cluster size",
        "operator",
        at=NOW - timedelta(days=1),
    )
    outcome = run_intake(intake_ctx(clean_proposal(), fence=fence))
    assert outcome.first_refusal.code == "registered_at_unstampable"


def test_after_registration_the_fence_opens():
    fence = QueryFence()
    key = "insider_dealing|main market and growth market listings above the tradability floor"
    fence.register_population(key, NOW - timedelta(days=2))
    fence.record(QueryKind.CONDITIONAL_RETURN, key, "CAR", "operator", at=NOW)
    assert fence.breach(key) is None


# ---------------------------------------------------------------------------
# The import fence.
# ---------------------------------------------------------------------------


def test_discovery_reaches_no_prices_or_outcomes():
    assert_import_fence("fntn.scanner.discovery")


def test_import_fence_would_catch_a_breach(monkeypatch):
    import fntn.scanner.fences as fences

    monkeypatch.setattr(fences, "FORBIDDEN_TO_DISCOVERY", {"json"})
    with pytest.raises(ImportFenceBreach):
        fences.assert_import_fence("fntn.scanner.discovery")


# ---------------------------------------------------------------------------
# Fail-fast, and the obligation attached to it.
# ---------------------------------------------------------------------------


def test_fail_fast_stops_at_the_first_failed_point():
    p = clean_proposal(event_definition="", measured_on_intention="")
    outcome = run_intake(intake_ctx(p, source_resolved=False))
    assert len(outcome.refusals) == 1
    assert outcome.first_refusal.code == "event_definition_absent"


def test_full_panel_reaches_every_later_point():
    p = clean_proposal(event_definition="", measured_on_intention="")
    outcome = run_intake(intake_ctx(p, source_resolved=False), mode=Mode.FULL_PANEL)
    emitted = {r.code for r in outcome.refusals}
    assert {"event_definition_absent", "measured_on_absent", "source_inaccessible"} <= emitted
    assert len(outcome.checks_reached) == len(codes.INTAKE_ORDER)


def test_every_abort_writes_a_rendered_summary():
    outcome = run_intake(intake_ctx(clean_proposal(event_definition="")))
    r = outcome.first_refusal
    assert r.summary and r.summary.count(".") >= 2
    assert "not recorded" not in r.summary
    assert r.code in codes.ALL_CODES


def test_audit_stream_is_deterministic_and_replayable():
    runner = intake_runner(parameter_hash="hash-A", audit_fraction=0.10)
    twin = intake_runner(parameter_hash="hash-A", audit_fraction=0.10)
    ids = [f"prop-{i:05d}" for i in range(2000)]
    assert [runner.in_audit_stream(i) for i in ids] == [twin.in_audit_stream(i) for i in ids]
    rate = sum(runner.in_audit_stream(i) for i in ids) / len(ids)
    assert 0.07 < rate < 0.13


def test_ordering_is_pre_registered_and_complete():
    ordered = set(codes.INTAKE_ORDER)
    defined = {rc.code for rc in codes.by_surface(codes.Surface.INTAKE)}
    # Two empty sets are equal. The panel's size is stated so this cannot pass
    # by both sides being empty, and so a point added or removed is legible.
    assert len(ordered) == 12
    # Every intake code is either a position or declared non-positional, and
    # nothing is both. `intake_budget_exhausted` is the one non-positional
    # code: a ceiling on time is an interruption, not a thirteenth check, and
    # giving it a position would put it in §13 row 23's distribution.
    assert codes.INTAKE_NON_POSITIONAL == {"intake_budget_exhausted"}
    assert not (ordered & codes.INTAKE_NON_POSITIONAL)
    assert ordered | codes.INTAKE_NON_POSITIONAL == defined
    with pytest.raises(ValueError):
        from fntn.scanner.ingest import Runner, build_intake_checks

        Runner("intake", codes.INTAKE_ORDER[:-1], build_intake_checks())


# ---------------------------------------------------------------------------
# Screen, directive, registration.
# ---------------------------------------------------------------------------


def make_record(event_class="insider_dealing", origin=Origin.AGENT) -> IntakeRecord:
    return IntakeRecord(
        intake_id="s1",
        origin=origin,
        event_definition="a mechanism",
        event_class=event_class,
        measured_on="a stated population",
        source_ref="external://x",
        source_partition=Partition.EXTERNAL,
        claims={"source_ref": ClaimField("source_ref", "x", Provenance.VERIFIED_PRIMARY)},
    )


def test_pointer_tier_is_computed_not_asserted():
    rec = make_record()
    assert rec.compute_evidence_tier().value == "pointer"


def test_not_applicable_checks_are_recorded_and_never_a_pass():
    result = screen_pointer(make_record())
    assert result.check_states[1] == "not_applicable_pointer_tier"
    assert result.check_states[4] == "not_applicable_pointer_tier"
    assert any(r.code == "check_not_applicable_pointer_tier" for r in result.refusals)


def test_check_three_is_binding():
    result = screen_pointer(make_record(event_class="lunar_phase"))
    assert not result.passed
    assert result.refusals[-1].code == "no_observable_stream"


def test_agent_evidence_routes_advisory_only():
    assert "advisory_only" in screen_pointer(make_record()).provenance_route


def test_new_subscription_is_deferred_and_the_feed_is_logged():
    draft = build_directive(
        make_record(event_class="index_reconstitution"),
        "dir-1",
        SegmentSpan(date(2024, 1, 1), date(2024, 7, 1), "pop"),
        30,
        ScoringMode.CROSS_MARKET,
    )
    assert draft.directive is None
    assert draft.refusals[0].code == "stream_requires_new_subscription"
    assert draft.declined_feed


def test_unclassified_waits_on_the_operator():
    draft = build_directive(
        make_record(event_class="unclassified"),
        "dir-1",
        SegmentSpan(date(2024, 1, 1), date(2024, 7, 1), "pop"),
        30,
        ScoringMode.CROSS_MARKET,
    )
    assert draft.directive is None
    assert draft.refusals[0].code == "stream_unmapped_pending_operator"


def test_manual_capacity_exhausted():
    draft = build_directive(
        make_record(event_class="short_interest_disclosure"),
        "dir-1",
        SegmentSpan(date(2024, 1, 1), date(2024, 7, 1), "pop"),
        30,
        ScoringMode.CROSS_MARKET,
        manual_capacity_remaining=0,
    )
    assert draft.refusals[0].code == "manual_observation_capacity_exhausted"


def _directive(origin=Origin.AGENT, days=180, pop="pop") -> Directive:
    return Directive(
        directive_id="dir-1",
        intake_id="s1",
        origin=origin,
        event_class="insider_dealing",
        measured_on=pop,
        stream="RNS PDMR notifications",
        stream_status=StreamStatus.SUBSCRIBED,
        stream_provenance=StreamProvenance.TABLE,
        scoring_mode=ScoringMode.CROSS_MARKET,
        span=SegmentSpan(date(2024, 1, 1), date(2024, 1, 1) + timedelta(days=days), pop),
        n_min=30,
    )


def test_registration_blocks_on_what_only_the_operator_supplies():
    blocking = register(_directive(), RegistrationInputs(), 25.0, NOW)
    emitted = {r.code for r in blocking}
    assert {"delta_min_absent", "premortem_unratified", "literature_search_absent"} <= emitted


def test_registration_reports_every_blocker_not_just_the_first():
    """Registration is deliberately not fail-fast: its output is a worklist."""

    assert len(register(_directive(), RegistrationInputs(), 25.0, NOW)) >= 3


def test_delta_min_below_floor_is_refused():
    blocking = register(
        _directive(),
        RegistrationInputs(
            delta_min=5.0,
            pre_mortem=PreMortem("confound", True, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    assert [r.code for r in blocking] == ["delta_min_below_floor"]


def test_unmeasurable_confound_refuses_before_the_segment_is_spent():
    blocking = register(
        _directive(),
        RegistrationInputs(
            delta_min=40.0,
            pre_mortem=PreMortem("unobservable flow", False, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    assert any(r.code == "confound_unmeasurable" for r in blocking)


def test_agent_drafted_premortem_blocks_until_ratified():
    blocking = register(
        _directive(),
        RegistrationInputs(
            delta_min=40.0,
            pre_mortem=PreMortem("confound", True, "agent", ratified_by_operator=False),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    assert [r.code for r in blocking] == ["premortem_unratified"]


def test_complete_registration_succeeds():
    d = _directive()
    assert register(
        d,
        RegistrationInputs(
            delta_min=40.0,
            registered_sign=1,
            pre_mortem=PreMortem("confound", True, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    ) == []
    assert d.is_registered


# ---------------------------------------------------------------------------
# Segment arithmetic.
# ---------------------------------------------------------------------------


def _registered(directive):
    register(
        directive,
        RegistrationInputs(
            delta_min=40.0,
            registered_sign=1,
            pre_mortem=PreMortem("c", True, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    return directive


def test_calibrations_hold_first_claim_on_the_segment():
    ledger = ReuseLedger(SegmentPolicy(segment_sessions=252, calibration_reserve_sessions=240))
    refusal = ledger.admit(_registered(_directive(days=180)))
    assert refusal.code == "segment_reserved_for_calibration"


def test_overlap_above_theta_is_refused():
    ledger = ReuseLedger(SegmentPolicy(theta=0.25, segment_sessions=2000))
    a = _registered(_directive())
    assert ledger.admit(a) is None
    b = _registered(_directive())
    b.directive_id = "dir-2"
    refusal = ledger.admit(b)
    assert refusal.code == "segment_overlap_exceeds_theta"


def test_disjoint_populations_do_not_overlap():
    ledger = ReuseLedger(SegmentPolicy(theta=0.25, segment_sessions=2000))
    assert ledger.admit(_registered(_directive(pop="pop-a"))) is None
    b = _registered(_directive(pop="pop-b"))
    b.directive_id = "dir-2"
    assert ledger.admit(b) is None


def test_agent_drafts_queue_and_may_not_displace():
    ledger = ReuseLedger(SegmentPolicy(theta=0.25, segment_sessions=2000))
    ledger.admit(_registered(_directive(origin=Origin.OPERATOR)))
    agent = _registered(_directive(origin=Origin.AGENT))
    agent.directive_id = "dir-2"
    assert ledger.admit(agent).code == "segment_overlap_exceeds_theta"
    assert ledger.enqueue(agent).code == "queued_behind_capacity"
    with pytest.raises(PermissionError):
        ledger.displace(agent, "dir-1", summaries.render("queued_behind_capacity", "x", {}))


def test_operator_displacement_requires_an_authored_summary():
    ledger = ReuseLedger(SegmentPolicy(theta=0.25, segment_sessions=2000))
    ledger.admit(_registered(_directive(origin=Origin.OPERATOR)))
    incoming = _registered(_directive(origin=Origin.OPERATOR))
    incoming.directive_id = "dir-2"
    with pytest.raises(ValueError):
        ledger.displace(
            incoming, "dir-1", summaries.render("queued_behind_capacity", "x", {})
        )
    authored = summaries.operator_authored(
        "queued_behind_capacity",
        "dir-1",
        "I am retiring the incumbent directive because its stream stopped "
        "publishing per-item timestamps in July. The incoming directive tests "
        "the same mechanism on a stream that still does.",
        "operator",
        {},
    )
    ledger.displace(incoming, "dir-1", authored)
    assert "dir-2" in ledger.open_directives


def test_queue_admits_by_smallest_span_first():
    ledger = ReuseLedger(SegmentPolicy(theta=1.0, segment_sessions=60))
    wide = _registered(_directive(days=300, pop="a"))
    narrow = _registered(_directive(days=30, pop="b"))
    narrow.directive_id = "dir-narrow"
    ledger.enqueue(wide)
    ledger.enqueue(narrow)
    assert ledger.queue[0].directive_id == "dir-narrow"


# ---------------------------------------------------------------------------
# Observation ingestion, surface B.
# ---------------------------------------------------------------------------


def _item(**overrides) -> Item:
    base = dict(
        item_id="itm-1",
        source_ref="rns://1",
        partition=Partition.DESIGN,
        document_type="static",
        t_pub_earliest=NOW,
        t_pub_earliest_provenance="feed_timestamp",
        t_pub_observed=NOW,
        extraction_class="regulatory_filing",
        extracted={"direction": "long", "direction_basis": "stated", "issuer": "resolved"},
        issuer="resolved",
        catalyst_duration_sessions=3,
        ingestion_lag_sessions=0,
    )
    base.update(overrides)
    return Item(**base)


def obs_ctx(item, directive=None, **overrides):
    d = directive or _registered(_directive())
    base = dict(
        item=item,
        directive=d,
        source_resolved=True,
        suspended_classes=frozenset(),
        lag_ceiling_sessions=1,
        admissible_horizon=5,
    )
    base.update(overrides)
    return ObservationContext(**base)


@pytest.mark.parametrize(
    "kwargs,extra,expected",
    [
        ({}, {"source_resolved": False}, "item_source_inaccessible"),
        ({"document_type": "running"}, {}, "running_document_no_anchor"),
        ({"t_pub_earliest_provenance": None}, {}, "anchor_provenance_absent"),
        ({"t_pub_observed": None}, {}, "observation_anchor_absent"),
        ({"ingestion_lag_sessions": 9}, {}, "ingestion_lag_exceeds_window"),
        ({}, {"suspended_classes": frozenset({"regulatory_filing"})}, "extraction_class_suspended"),
        ({"extracted": {"direction": "long"}}, {}, "extraction_schema_incomplete"),
        ({"issuer": None}, {}, "issuer_unresolved"),
        ({"t_cat_claimed": NOW}, {}, "catalyst_date_corroborated"),
        ({"catalyst_duration_sessions": 0}, {}, "catalyst_duration_below_floor"),
    ],
)
def test_observation_points_fail_fast_with_the_right_code(kwargs, extra, expected):
    outcome = observation_runner().run(
        "itm-1", obs_ctx(_item(**kwargs), **extra), mode=Mode.FAIL_FAST
    )
    assert not outcome.passed
    assert outcome.first_refusal.code == expected
    assert len(outcome.refusals) == 1


def test_observation_before_registration_is_inadmissible():
    d = _registered(_directive())
    d.registered_at = NOW + timedelta(days=10)
    outcome = observation_runner().run("itm-1", obs_ctx(_item(), directive=d))
    assert outcome.first_refusal.code == "observation_precedes_registration"


def test_a_clean_item_passes_every_point():
    outcome = observation_runner().run("itm-clean", obs_ctx(_item()))
    assert outcome.passed
    assert len(outcome.checks_reached) == len(codes.OBSERVATION_ORDER)


# ---------------------------------------------------------------------------
# Discovery and the control arm.
# ---------------------------------------------------------------------------


def test_sweep_is_cached_by_content_hash():
    payload = {"proposals": [{"event_definition": "a mechanism", "measured_on_intention": "pop", "event_class": "insider_dealing", "source_ref": "external://x"}]}
    client = StubClient([payload, payload])
    corpus = Corpus("c1", Partition.EXTERNAL, ["doc"])
    fence, cache = QueryFence(), ProposalCache()
    first = sweep(client, corpus, fence, cache, now=NOW)
    second = sweep(client, corpus, fence, cache, now=NOW)
    assert client.calls == 1
    assert not first.cache_hit and second.cache_hit


def test_sweep_logs_every_read_to_the_query_fence():
    client = StubClient([{"proposals": []}])
    fence = QueryFence()
    sweep(client, Corpus("c1", Partition.EXTERNAL, ["d"]), fence, ProposalCache(), now=NOW)
    assert fence.log[0].kind is QueryKind.MECHANISM_LEVEL


def test_system_prompt_states_the_binding_rules():
    for phrase in ("MECHANISMS, never EPISODES", "unclassified", "Do not score merit"):
        assert phrase in SYSTEM_PROMPT


def test_control_draw_is_seeded_and_replayable():
    grid = [
        GridCell("insider_dealing", "pop-a", "a drawn mechanism"),
        GridCell("buyback", "pop-b", "another drawn mechanism"),
    ]
    a = draw_control_mechanisms(grid, 8, seed=7, now=NOW)
    b = draw_control_mechanisms(grid, 8, seed=7, now=NOW)
    # An arm of zero would make both assertions below true whilst meaning the
    # control arm had not been drawn at all, which is the one outcome §13
    # row 20 exists to prevent.
    assert len(a) == 8 and len(b) == 8
    assert [p.drawn_from_grid_cell for p in a] == [p.drawn_from_grid_cell for p in b]
    assert all(p.origin is Origin.RANDOM_CONTROL for p in a)


def test_control_arm_reports_undetermined_rather_than_passing_by_want_of_power():
    v = ControlArmVerdict(agent_n=5, control_n=5, n_min=30, delta=20.0, separation=100.0)
    assert v.verdict() == "undetermined_at_budget"


def test_control_arm_can_refute_the_discovery_layer():
    v = ControlArmVerdict(agent_n=50, control_n=50, n_min=30, delta=20.0, separation=2.0)
    assert v.verdict().startswith("killed_negligible")


# ---------------------------------------------------------------------------
# Rejection summaries.
# ---------------------------------------------------------------------------


def test_summary_is_rendered_from_the_records_own_fields():
    r = summaries.render("delta_min_below_floor", "dir-1", {"delta_min": 5.0, "delta_min_floor": 25.0})
    assert "5.0" in r.summary and "25.0" in r.summary
    assert r.author == "template"


def test_operator_authored_summary_must_be_two_to_three_sentences():
    with pytest.raises(ValueError):
        summaries.operator_authored("no_observable_stream", "s1", "Too short.", "operator", {})


def test_unknown_code_cannot_be_emitted():
    with pytest.raises(ValueError):
        summaries.render("invented_code", "s1", {})


def test_coverage_rejects_codes_from_outside_the_registry():
    with pytest.raises(ValueError):
        codes.coverage(["invented_code"])


# ---------------------------------------------------------------------------
# End to end.
# ---------------------------------------------------------------------------


def test_end_to_end_scan_produces_a_legible_ledger():
    payload = {
        "proposals": [
            {
                "event_definition": "clusters of open-market director purchases within five sessions",
                "measured_on_intention": "growth-market listings above the tradability floor",
                "event_class": "insider_dealing",
                "source_ref": "external://register/a",
            },
            {
                "event_definition": "purchases following the pattern at Acme Holdings PLC",
                "measured_on_intention": "growth-market listings",
                "event_class": "insider_dealing",
                "source_ref": "external://register/b",
            },
            {
                "event_definition": "reductions in issued share capital by tender",
                "measured_on_intention": "main-market listings",
                "event_class": "index_reconstitution",
                "source_ref": "external://register/c",
            },
            {
                "event_definition": "changes in lunar illumination preceding disclosure",
                "measured_on_intention": "all listings",
                "event_class": "lunar_phase",
                "source_ref": "external://register/d",
            },
        ]
    }
    ledger = Ledger(parameter_hash="test")
    config = ScanConfig(
        parameter_hash="test",
        entity_fence=FENCE,
        exclusivity={
            "insider_dealing": ScoringMode.CROSS_MARKET,
            "buyback": ScoringMode.CROSS_MARKET,
            "index_reconstitution": ScoringMode.CROSS_MARKET,
            "lunar_phase": ScoringMode.CROSS_MARKET,
        },
        policy=SegmentPolicy(theta=0.25, segment_sessions=2000, delta_min_floor=25.0),
    )
    result = scan(
        StubClient([payload]),
        [Corpus("c1", Partition.EXTERNAL, ["doc"])],
        [GridCell("insider_dealing", "drawn population", "a drawn mechanism")],
        config,
        ledger,
        now=NOW,
    )

    assert result.proposed == 5  # four proposed, one drawn
    assert result.fence_report.import_fence_clean
    assert result.fence_report.entity_refusals == 1
    # Nothing reaches capital, and nothing is registered without the operator.
    assert result.admitted == []
    assert result.blocked_on_operator
    assert ledger.declined_feed_distribution()
    # Every abandonment carries its §8 summary. An empty abandoned list would
    # satisfy that loop whilst showing nothing, and a scan that abandoned
    # nothing is a different test from this one.
    assert len(result.abandoned) == 3
    for subject_id, _ in result.abandoned:
        assert ledger.summaries_for(subject_id)
    ledger.close()


def _scan_with(exclusivity, default=ScoringMode.CROSS_MARKET, control_ratio=0.25):
    payload = {
        "proposals": [
            {
                "event_definition": "clusters of open-market director purchases within five sessions",
                "measured_on_intention": "growth-market listings above the tradability floor",
                "event_class": "insider_dealing",
                "source_ref": "external://register/a",
            }
        ]
    }
    ledger = Ledger(parameter_hash="mode")
    config = ScanConfig(
        parameter_hash="mode",
        default_scoring_mode=default,
        entity_fence=FENCE,
        control_arm_ratio=control_ratio,
        exclusivity=exclusivity,
        policy=SegmentPolicy(theta=0.25, segment_sessions=2000, delta_min_floor=25.0),
    )
    result = scan(
        StubClient([payload]),
        [Corpus("c1", Partition.EXTERNAL, ["doc"])],
        [GridCell("insider_dealing", "drawn population", "a drawn mechanism")],
        config,
        ledger,
        now=NOW,
    )
    return result, ledger


def test_registered_default_applies_where_a_class_declares_none():
    result, ledger = _scan_with({"insider_dealing": None})
    directive = result.blocked_on_operator[0][0]
    assert directive.scoring_mode is ScoringMode.CROSS_MARKET
    # One proposed, one drawn: the control arm is never absent.
    assert result.fence_report.scoring_modes == {"cross_market": 2}
    ledger.close()


def test_a_sweep_without_a_control_arm_is_refused():
    """Unfalsifiable is refused, not floored."""

    with pytest.raises(ValueError, match="refute"):
        _scan_with({"insider_dealing": None}, control_ratio=0.0)


def test_per_class_override_beats_the_default():
    result, ledger = _scan_with({"insider_dealing": ScoringMode.FORWARD_ONLY})
    assert result.blocked_on_operator[0][0].scoring_mode is ScoringMode.FORWARD_ONLY
    ledger.close()


def test_default_settles_which_construction_never_whether_one_exists():
    """A class absent from the mapping is not discoverable, default or no default."""

    result, ledger = _scan_with({})
    assert result.blocked_on_operator == []
    assert result.abandoned[0][1].code == "scoring_mode_unsatisfiable"
    ledger.close()


def test_cross_market_assumption_is_disclosed_on_the_report():
    result, ledger = _scan_with({"insider_dealing": None})
    rendered = result.fence_report.render()
    assert "generalise across markets" in rendered
    assert "row 24" in rendered
    ledger.close()


def test_disjoint_partition_carries_no_generalisability_note():
    result, ledger = _scan_with(
        {"insider_dealing": None}, default=ScoringMode.DISJOINT_PARTITION
    )
    assert "generalise across markets" not in result.fence_report.render()
    ledger.close()


def test_every_defined_code_is_emitted(tmp_path):
    """The headline test: a code defined and never emitted is an untested branch.

    Assembled by running each refusal branch deliberately rather than by hoping
    a corpus happens to exercise them, because the failure class §9.4 exists to
    find is precisely a rule nothing ever reached.
    """

    ledger = Ledger(parameter_hash="coverage")

    # -- intake, full panel over a maximally defective proposal ------------
    fence = QueryFence()
    fence.record(QueryKind.CONDITIONAL_RETURN, "insider_dealing|pop", "CAR", "operator", at=NOW - timedelta(days=1))
    bad = clean_proposal(
        event_definition="",
        measured_on_intention="",
        event_class="insider_dealing",
        mechanism_note="Acme PLC in March 2024",
        source_partition=Partition.EVALUATION,
    )
    ctx = intake_ctx(
        bad,
        raw_payload={"delta_min": 1.0},
        fence=fence,
        source_resolved=False,
        open_pairs={("insider_dealing", ""): {"directive_id": "dir-x", "registered_at": "t"}},
        exclusivity_available={},
        claim_provenance={"a": None, "b": "recollection"},
    )
    ledger.write_refusals(run_intake(ctx, mode=Mode.FULL_PANEL).refusals)

    # security_master_unavailable: the fence's binding layer with no master.
    ledger.write_refusals(
        run_intake(
            intake_ctx(clean_proposal(), entity_fence=DEFAULT_FENCE),
            mode=Mode.FULL_PANEL,
        ).refusals
    )

    # registered_at_unstampable needs a matching population key.
    f2 = QueryFence()
    f2.record(QueryKind.CONDITIONAL_RETURN, "insider_dealing|pop", "CAR", "operator", at=NOW - timedelta(days=1))
    p2 = clean_proposal(measured_on_intention="pop")
    ledger.write_refusals(run_intake(intake_ctx(p2, fence=f2), mode=Mode.FULL_PANEL).refusals)

    # -- intake, abandoned to the registered ceiling -----------------------
    # A clock that steps past the point budget on every call, so the first
    # check over-runs, its one retry over-runs, and the subject is abandoned.
    ledger.write_refusals(
        run_intake(
            intake_ctx(clean_proposal()),
            mode=Mode.FULL_PANEL,
            budget=MeasuringBudget(
                point_budget_s=20.0, subject_budget_s=120.0, retry_max=1,
                clock=itertools.count(0.0, 30.0).__next__,
            ),
        ).refusals
    )

    # -- screen ------------------------------------------------------------
    ledger.write_refusals(screen_pointer(make_record(event_class="lunar_phase")).refusals)
    ledger.write_refusals(screen_pointer(make_record()).refusals)

    # -- directive ---------------------------------------------------------
    span = SegmentSpan(date(2024, 1, 1), date(2024, 7, 1), "pop")
    for cls in ("index_reconstitution", "unclassified", "short_interest_disclosure"):
        ledger.write_refusals(
            build_directive(make_record(event_class=cls), "dir-1", span, 30, ScoringMode.CROSS_MARKET).refusals
        )

    # -- registration ------------------------------------------------------
    ledger.write_refusals(register(_directive(), RegistrationInputs(), 25.0, NOW))
    ledger.write_refusals(
        register(
            _directive(),
            RegistrationInputs(delta_min=5.0, pre_mortem=PreMortem("c", True, "operator", True), literature_search_ref="r"),
            25.0,
            NOW,
        )
    )
    ledger.write_refusals(
        register(
            _directive(),
            RegistrationInputs(delta_min=40.0, pre_mortem=PreMortem("c", False, "operator", True), literature_search_ref="r"),
            25.0,
            NOW,
        )
    )

    # -- segment -----------------------------------------------------------
    tight = ReuseLedger(SegmentPolicy(segment_sessions=252, calibration_reserve_sessions=250))
    ledger.write_refusal(tight.admit(_registered(_directive())))
    wide = ReuseLedger(SegmentPolicy(theta=0.25, segment_sessions=2000))
    wide.admit(_registered(_directive()))
    second = _registered(_directive())
    second.directive_id = "dir-2"
    ledger.write_refusal(wide.admit(second))
    ledger.write_refusal(wide.enqueue(second))

    # -- observation, full panel over a maximally defective item ----------
    d = _registered(_directive())
    d.registered_at = NOW + timedelta(days=10)
    defective = _item(
        document_type="running",
        t_pub_earliest_provenance=None,
        ingestion_lag_sessions=99,
        extracted={"direction": "long"},
        issuer=None,
        t_cat_claimed=NOW,
        catalyst_duration_sessions=0,
    )
    ledger.write_refusals(
        observation_runner()
        .run("itm-bad", obs_ctx(defective, directive=d, source_resolved=False, suspended_classes=frozenset({"regulatory_filing"})), mode=Mode.FULL_PANEL)
        .refusals
    )
    # observation_anchor_absent needs t_pub_observed missing on its own.
    ledger.write_refusals(
        observation_runner()
        .run("itm-noobs", obs_ctx(_item(t_pub_observed=None)), mode=Mode.FULL_PANEL)
        .refusals
    )

    report = codes.coverage(ledger.emitted_codes())
    assert report.never_emitted == [], (
        "codes defined but never emitted -- untested branches: "
        + ", ".join(report.never_emitted)
    )
    assert report.ratio == 1.0
    ledger.close()


# ---------------------------------------------------------------------------
# Registration and the security master.
# ---------------------------------------------------------------------------

from fntn.scanner.master import SecurityMaster
from fntn.scanner.params import (
    Corpus as RegCorpus,
    DiscoverableClass,
    Registration,
    RegistrationHashMismatch,
    RegistrationHistoryMissing,
    RegistrationIncomplete,
)


def _complete_registration(**over) -> Registration:
    base = dict(
        control_arm_delta=50.0, control_arm_n_min=30,
        control_arm_ratio=0.25, control_arm_seed=20260826,
        corpora=[RegCorpus("asx", "ASX", "external", "./corpora/asx")],
        discoverable_classes=[DiscoverableClass("insider_dealing")],
        security_master_files=["master.csv"],
        theta=0.25, delta_min_floor=25.0,
        registered_at="2026-08-26T00:00:00+00:00", registered_by="operator",
    )
    base.update(over)
    return Registration(**base)


def test_blank_registration_names_every_gap_at_once():
    gaps = Registration.blank().missing()
    assert len(gaps) >= 10
    assert any("control_arm_delta" in g for g in gaps)
    assert any("theta" in g for g in gaps)


def test_sweep_refuses_on_an_incomplete_registration():
    with pytest.raises(RegistrationIncomplete, match="not a kill criterion"):
        Registration.blank().require_complete()


def test_complete_registration_passes():
    assert _complete_registration().missing() == []


def test_control_arm_ratio_of_zero_is_refused_at_registration():
    assert any("exceed zero" in g for g in _complete_registration(control_arm_ratio=0).missing())


def test_kill_threshold_may_not_sit_below_the_floor():
    gaps = _complete_registration(control_arm_delta=10.0, delta_min_floor=25.0).missing()
    assert any("below delta_min_floor" in g for g in gaps)


def test_scored_partitions_are_refused_in_a_corpus_row():
    reg = _complete_registration(
        corpora=[RegCorpus("x", "LSE", "evaluation", "./x")]
    )
    assert any("may not read" in g for g in reg.missing())


def test_registration_hash_changes_with_any_value():
    a = _complete_registration()
    b = _complete_registration(control_arm_seed=1)
    assert a.hash() != b.hash()


def test_rationale_is_prose_and_does_not_change_the_hash():
    a = _complete_registration()
    b = _complete_registration()
    b.rationale = "because"
    assert a.hash() == b.hash()


def test_a_stamp_cannot_be_moved():
    with pytest.raises(RegistrationIncomplete, match="cannot move"):
        _complete_registration().stamp("operator")


def test_discoverability_and_construction_are_separate_questions():
    """The class says whether; the corpus says which guarantee."""

    reg = _complete_registration()
    assert reg.is_discoverable("insider_dealing")
    assert not reg.is_discoverable("lunar_phase")
    assert reg.scoring_mode_for_corpus("asx") == "cross_market"
    assert reg.scoring_mode_for_corpus("nonexistent") is None


def test_master_indexes_names_and_strips_suffixes(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("Company Name,ASX Code\nAcme Holdings plc,ACM\nBarclays PLC,BARC\n")
    m = SecurityMaster()
    cov = m.load_csv(csv, market="ASX", listed_total=2)
    assert cov.rows == 2
    # Legal form stripped; "Holdings" retained, because it is a name component
    # and stripping it would reduce the name to a generic word.
    assert "acme holdings" in m.names and "acme holdings plc" in m.names
    assert "barclays" in m.names
    assert "barc" in m.tickers
    assert cov.coverage == 1.0


def test_master_refuses_a_file_it_cannot_read(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("alpha,beta\n1,2\n")
    with pytest.raises(ValueError, match="no name or ticker column"):
        SecurityMaster().load_csv(csv)


def test_unknown_coverage_is_not_treated_as_complete(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("Company,Ticker\nAcme plc,ACM\n")
    m = SecurityMaster()
    m.load_csv(csv, market="ASX")  # no listed_total
    assert m.readable_markets(0.95) == []
    assert "coverage unknown" in m.unreadable_markets(0.95)["ASX"]


def test_master_below_floor_is_unreadable(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("Company,Ticker\nAcme plc,ACM\n")
    m = SecurityMaster()
    m.load_csv(csv, market="ASX", listed_total=100)
    assert "below floor" in m.unreadable_markets(0.95)["ASX"]


def test_master_builds_a_working_fence(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("Company,Ticker\nVodafone Group plc,VOD\n")
    m = SecurityMaster(); m.load_csv(csv, market="LSE")
    f = m.as_fence()
    assert entity_mentions("purchases at Vodafone Group in the window", f)
    assert entity_mentions("notifications lodged with ASX under Listing Rule 12.9", f) == []


def test_fence_matches_multi_word_names_as_spans(tmp_path):
    """The binding layer was inert for any issuer whose name is more than one word."""

    csv = tmp_path / "m.csv"
    csv.write_text("Company,Ticker\nVodafone Group plc,VOD\nRio Tinto Limited,RIO\n")
    m = SecurityMaster(); m.load_csv(csv, market="LSE")
    f = m.as_fence()
    assert entity_mentions("purchases at Vodafone Group in the window", f)
    assert entity_mentions("directors of Rio Tinto filing late", f)
    assert entity_mentions("a mechanism with no issuer named at all", f) == []


def test_multi_market_csv_is_grouped_not_collapsed(tmp_path):
    """An earlier version reported the last market as covering every row."""

    csv = tmp_path / "m.csv"
    csv.write_text(
        "Company,Ticker,Market\n"
        "Vodafone Group plc,VOD,LSE\nBarclays PLC,BARC,LSE\n"
        "Rio Tinto Limited,RIO,ASX\nShopify Inc.,SHOP,TSX\n"
    )
    m = SecurityMaster(); m.load_csv(csv)
    assert set(m.per_market) == {"LSE", "ASX", "TSX"}
    assert m.per_market["LSE"].rows == 2
    assert m.per_market["ASX"].rows == 1
    # No per-market total can be inferred from a combined file, so coverage is
    # unknown, and unknown is not readable.
    assert m.readable_markets(0.95) == []


def test_named_market_override_still_attaches_the_total(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("Company,Ticker,Market\nAcme plc,ACM,IGNORED\n")
    m = SecurityMaster(); m.load_csv(csv, market="ASX", listed_total=1)
    assert set(m.per_market) == {"ASX"}
    assert m.per_market["ASX"].coverage == 1.0


def test_pre_archive_is_a_distinct_construction():
    """US discovery cannot be cross_market: the US is inside the traded universe."""

    assert ScoringMode.PRE_ARCHIVE.value == "pre_archive"
    assert len({m.value for m in ScoringMode}) == 4


def test_registration_refuses_an_unknown_scoring_mode():
    reg = _complete_registration(default_scoring_mode="wishful")
    assert any("not one of" in g for g in reg.missing())


def test_registration_refuses_an_unknown_corpus_mode():
    reg = _complete_registration(
        corpora=[RegCorpus("x", "ASX", "external", "./x", "sideways")]
    )
    assert any("sideways" in g for g in reg.missing())


def test_an_in_universe_corpus_may_not_claim_cross_market():
    """The one direction the mistake goes, and it voids the guarantee silently."""

    for venue in ("US", "NYSE", "EDGAR", "UK", "LSE", "AIM"):
        reg = _complete_registration(
            corpora=[RegCorpus("c", venue, "external", "./c", "cross_market")]
        )
        gaps = reg.missing()
        assert any("cannot provide cross_market" in g for g in gaps), venue


@pytest.mark.parametrize("venue", ["AU", "ASX", "EU", "Euronext", "NZ", "NZX"])
def test_an_external_corpus_may_claim_cross_market(venue):
    reg = _complete_registration(
        corpora=[RegCorpus("c", venue, "external", "./c", "cross_market")]
    )
    assert reg.missing() == []


@pytest.mark.parametrize("venue,mode", [("US", "pre_archive"), ("UK", "forward_only")])
def test_in_universe_corpora_accept_the_time_disjoint_constructions(venue, mode):
    reg = _complete_registration(
        corpora=[RegCorpus("c", venue, "external", "./c", mode)],
        archive_opens="2023-01-01",
    )
    assert reg.missing() == []


def test_every_named_market_resolves_from_its_venue_names():
    from fntn.scanner.markets import ALIASES, MARKETS, resolve

    assert set(MARKETS) == {"US", "UK", "AU", "EU", "NZ"}
    assert len(ALIASES) == 27, "an empty alias table would resolve nothing"
    for alias, code in ALIASES.items():
        assert resolve(alias).code == code, alias


def test_sec_ticker_file_loads_and_is_its_own_population(tmp_path):
    f = tmp_path / "company_tickers.json"
    f.write_text(json.dumps({
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corporation"},
    }))
    m = SecurityMaster()
    cov = m.load_sec_tickers(f)
    assert cov.rows == 2
    # The regulator's own file is the population, so coverage is complete by
    # construction rather than by estimate.
    assert cov.coverage == 1.0
    assert m.readable_markets(0.95) == ["US"]
    assert "apple" in m.names and "aapl" in m.tickers
    assert "microsoft" in m.names


def test_sec_master_fences_us_issuers(tmp_path):
    f = tmp_path / "company_tickers.json"
    f.write_text(json.dumps({
        "0": {"cik_str": 1, "ticker": "AAPL", "title": "Apple Inc."},
    }))
    m = SecurityMaster(); m.load_sec_tickers(f)
    fence = m.as_fence()
    assert entity_mentions("director purchases at Apple after the filing", fence)
    assert entity_mentions("Form 4 filings within two business days", fence) == []


def test_construction_is_a_property_of_the_corpus_not_the_class():
    """One class read from two markets carries two different guarantees."""

    from fntn.scanner.markets import construction_for

    assert construction_for("ASX") == ScoringMode.CROSS_MARKET
    assert construction_for("EDGAR") == ScoringMode.PRE_ARCHIVE
    assert construction_for("LSE") == ScoringMode.PRE_ARCHIVE
    assert construction_for("NZX") == ScoringMode.CROSS_MARKET
    reg = _complete_registration(
        corpora=[
            RegCorpus("au", "AU", "external", "./au", "cross_market"),
            RegCorpus("us", "US", "external", "./us", "pre_archive"),
        ],
        archive_opens="2023-01-01",
    )
    assert reg.missing() == []
    assert reg.scoring_mode_for_corpus("au") == "cross_market"
    assert reg.scoring_mode_for_corpus("us") == "pre_archive"


def test_pre_archive_requires_a_stated_boundary():
    """Without archive_opens the mode names nothing and is a label."""

    reg = _complete_registration(
        corpora=[RegCorpus("us", "US", "external", "./us", "pre_archive")]
    )
    assert any("archive_opens is not set" in g for g in reg.missing())
    reg.archive_opens = "2023-01-01"
    assert reg.missing() == []


def test_cross_market_needs_no_archive_boundary():
    reg = _complete_registration(
        corpora=[RegCorpus("au", "AU", "external", "./au", "cross_market")]
    )
    assert reg.archive_opens is None
    assert reg.missing() == []


# ---------------------------------------------------------------------------
# The registration's own history.
#
# A hash on a record is a promise that the object it was taken over can be
# recovered.  Until docs/REGISTRATION_HISTORY.md existed the promise was false
# for every superseded hash, because `save` overwrote the file and the chain
# was recorded nowhere.  These tests are what makes the document a record
# rather than a claim: every row is recomputed from the object it names, under
# the dataclass of the commit it names, and a row that does not recompute fails
# here rather than warning.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_MD = REPO_ROOT / "docs" / "REGISTRATION_HISTORY.md"
REGISTRATION_FILE = "discovery_registration.json"


def _history_rows():
    """Parse the chain table.  A malformed table is a failure, not zero rows.

    Returning an empty list on a table this cannot read would make the whole
    suite below vacuous, which is the failure mode a provenance test can least
    afford: it would pass loudest exactly when the record had been broken.
    """

    rows = []
    for line in HISTORY_MD.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or not cells[0].isdigit():
            continue
        rows.append(
            {
                "n": int(cells[0]),
                "hash": cells[1].strip("`"),
                "stamped": cells[2],
                "commit": cells[3].strip("`*"),
                "object": cells[4],
                "provenance": cells[5],
                "field": cells[6],
            }
        )
    assert rows, f"no chain rows parsed from {HISTORY_MD}"
    assert [r["n"] for r in rows] == list(range(1, len(rows) + 1))
    return rows


def _git(*args) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True, capture_output=True, text=True,
    ).stdout


def _hash_under(commit: str, blob: bytes, tmp: Path) -> str:
    """Recompute a registration hash under the dataclass of ``commit``.

    The code has to come from the commit, not from the working tree. A hash is
    taken over the field set as well as the values, so the 26 August object
    hashes to `a06400ef28ebb54c` under the schema it was stamped under and to
    something else under today's, whilst being the same bytes throughout. A
    test that recomputed with today's `Registration` would fail every
    historical row and would be measuring the wrong thing when it did.
    """

    work = tmp / commit
    work.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", commit, "src"],
        check=True, capture_output=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(work)], input=tar, check=True)
    (work / "r.json").write_bytes(blob)
    out = subprocess.run(
        [sys.executable, "-c",
         "from fntn.scanner.params import Registration;"
         "print(Registration.load('r.json').hash())"],
        cwd=work, check=True, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    return out.stdout.strip()


def _row_object(row, tmp: Path) -> bytes:
    """The bytes the row names, from git or from the tree."""

    cell = row["object"]
    if cell.startswith("`git show "):
        ref = cell.split("`git show ", 1)[1].split("`", 1)[0]
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", ref],
            check=True, capture_output=True,
        ).stdout
    path = cell.strip("`").split("`", 1)[0]
    if path.startswith("docs/"):
        return (REPO_ROOT / path).read_bytes()
    return (REPO_ROOT / REGISTRATION_FILE).read_bytes()


def test_every_history_row_names_the_registration_file():
    """`save` looks for a line carrying both the hash and the file.

    A row that names the hash and not the file would let the overwrite through
    without recording what was overwritten.
    """

    for row in _history_rows():
        assert REGISTRATION_FILE in row["object"], row


def test_registration_history_recomputes(tmp_path):
    """Every hash in the chain, recomputed from the object the row names.

    This is the whole of what makes the file a record. A row that does not
    recompute is a hash nothing in the repository accounts for, which is the
    state the file exists to end, so it fails here rather than warning.
    """

    for row in _history_rows():
        blob = _row_object(row, tmp_path)
        if row["commit"] == "current":
            got = Registration.load(REPO_ROOT / REGISTRATION_FILE).hash()
        else:
            got = _hash_under(row["commit"], blob, tmp_path)
        assert got == row["hash"], (
            f"row {row['n']}: {row['object']} under {row['commit']} hashes to "
            f"{got}, and the history says {row['hash']}"
        )


def test_a_superseded_row_carries_its_object_commit():
    """Only the newest row may say `current`, and it must be the newest.

    The current row is completed with a SHA when it is superseded. A row left
    on `current` behind a newer one is a version whose object was overwritten
    with nothing recording where it went, which is the original defect.
    """

    rows = _history_rows()
    assert len(rows) >= 2, "a chain of one exercises neither half of this"
    for row in rows[:-1]:
        assert row["commit"] != "current", row
    assert rows[-1]["commit"] == "current"


def test_the_registration_in_the_tree_is_the_newest_row():
    """The file and the chain agree, and the file says so itself."""

    rows = _history_rows()
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.hash() == rows[-1]["hash"]
    assert reg.registered_hash == rows[-1]["hash"]
    assert reg.registered_at.startswith(rows[-1]["stamped"])


def test_every_causing_field_names_a_real_field_or_the_first_stamp():
    fields = {f.name for f in dataclasses.fields(Registration)}
    for row in _history_rows():
        cell = row["field"].strip("`")
        assert cell in fields or cell.startswith("n/a"), row


# -- the overwrite guard itself ---------------------------------------------


def _stamped(tmp_path, **over) -> Path:
    reg = _complete_registration(**over)
    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir(exist_ok=True)
    reg.save(p)
    return p


def test_save_refuses_to_overwrite_a_stamped_registration_unrecorded(tmp_path):
    """Rule 4 reaches the registration, which was exempt from its own rule."""

    p = _stamped(tmp_path)
    later = _complete_registration(control_arm_seed=1)
    with pytest.raises(RegistrationHistoryMissing, match="destroy the object"):
        later.save(p)
    # And the file that would have been destroyed is still there, unchanged.
    assert Registration.load(p).control_arm_seed == 20260826


def test_save_proceeds_once_the_prior_hash_and_path_are_recorded(tmp_path):
    p = _stamped(tmp_path)
    prior = Registration.load(p).registered_hash
    hist = tmp_path / "docs" / "REGISTRATION_HISTORY.md"
    hist.write_text(f"| 1 | `{prior}` | `{REGISTRATION_FILE}` |\n")
    later = _complete_registration(control_arm_seed=1)
    assert later.save(p) == later.hash()
    assert Registration.load(p).control_arm_seed == 1


def test_a_row_naming_the_hash_but_not_the_file_does_not_release_the_guard(tmp_path):
    p = _stamped(tmp_path)
    prior = Registration.load(p).registered_hash
    hist = tmp_path / "docs" / "REGISTRATION_HISTORY.md"
    hist.write_text(f"| 1 | `{prior}` | some other object |\n")
    with pytest.raises(RegistrationHistoryMissing):
        _complete_registration(control_arm_seed=1).save(p)


def test_an_unstamped_form_may_be_written_over_freely(tmp_path):
    """A blank form is not a commitment, and nothing is destroyed by filling it."""

    p = tmp_path / REGISTRATION_FILE
    Registration.blank().save(p)
    assert _complete_registration().save(p)


def test_rewriting_the_same_values_is_not_an_overwrite(tmp_path):
    p = _stamped(tmp_path)
    same = _complete_registration()
    assert same.save(p) == same.hash()


def test_a_prior_without_a_recorded_hash_refuses_rather_than_recomputing(tmp_path):
    """The file says, or nobody does.

    Recomputing would answer a different question, namely what those bytes hash
    to under today's dataclass, and for every registration written before the
    last schema change that is not the hash its records carry.
    """

    p = tmp_path / REGISTRATION_FILE
    raw = json.loads(_complete_registration().save(p) and p.read_text())
    raw.pop("registered_hash")
    p.write_text(json.dumps(raw))
    with pytest.raises(RegistrationHistoryMissing, match="does not record the hash"):
        _complete_registration(control_arm_seed=1).save(p)


def test_a_stated_prior_hash_is_an_assertion_the_file_may_refute(tmp_path):
    p = _stamped(tmp_path)
    with pytest.raises(RegistrationHistoryMissing, match="disagreement is"):
        _complete_registration(control_arm_seed=1).save(p, prior_hash="deadbeefdeadbeef")


# -- the lexicon now reaches the hash ---------------------------------------


def test_the_lexicon_reaches_the_hash():
    """Adding a lexicon row is a re-stamp.  That is the cost, and the point.

    Until this landed the lexicon was a module constant, so two runs under one
    hash could refuse two different sets of tokens and could load two different
    security masters, the loader filtering the ticker set against it as well.
    """

    a = _complete_registration()
    b = _complete_registration(lexicon=sorted(SEED_LEXICON | {"gadget"}))
    assert a.hash() != b.hash()


def test_the_registered_lexicon_seeds_from_the_module_constant():
    assert set(_complete_registration().lexicon) == set(SEED_LEXICON)


def test_registered_hash_is_provenance_and_is_not_hashed():
    """It records this function's own result, so hashing it would be circular."""

    a = _complete_registration()
    b = _complete_registration()
    b.registered_hash = "not a hash"
    assert a.hash() == b.hash()


def test_the_master_filters_against_the_registered_lexicon(tmp_path):
    """The loader's copy and the fence's copy have to be one list.

    A token in the lexicon never enters the master at all, so the lexicon
    decides what the fence CAN SEE as well as what it ignores. A master loaded
    under the module seed whilst the fence ran on a registered list would
    refuse a set neither list explains.
    """

    csv = tmp_path / "m.csv"
    csv.write_text("Company Name,Ticker\nGadget Industries plc,GDGT\n")
    wide = SecurityMaster(lexicon=frozenset({"gdgt"}))
    wide.load_csv(csv, market="US", listed_total=1)
    assert "gdgt" not in wide.tickers
    assert "gadget industries" in wide.names
    assert wide.as_fence().lexicon == frozenset({"gdgt"})


# ---------------------------------------------------------------------------
# The corpus can be re-derived from what the server sent.
#
# Extraction is destructive: it rewrites the fetched page as its own text. Until
# the raw bytes were kept, `raw_bytes` in the manifest was a number with nothing
# behind it, a change to the extractor could be tested only against itself, and
# the claim that the corpus IS the material rested on a fetch nobody could
# repeat. corpora/us/_raw holds the pages; this is the round trip.
# ---------------------------------------------------------------------------

RAW_DIR = REPO_ROOT / "corpora" / "us" / "_raw"
FETCH_SCRIPT = REPO_ROOT / "scripts_fetch_us_corpus.sh"


def _script_extractor(tmp: Path) -> Path:
    """The extractor as the fetch script defines it, not a copy of it.

    Pulled out of the heredoc so that a divergence between the script and this
    test is impossible rather than merely unlikely: a test that reimplemented
    the extraction would pass whilst the corpus was produced by something else.
    """

    text = FETCH_SCRIPT.read_text().splitlines(keepends=True)
    try:
        start = next(i for i, l in enumerate(text)
                     if l.startswith('cat > "$EXTRACTOR" <<')) + 1
        end = next(i for i, l in enumerate(text[start:], start)
                   if l.rstrip("\n") == "EXTRACTPY")
    except StopIteration:  # pragma: no cover - a structural change to the script
        raise AssertionError(f"no EXTRACTPY heredoc found in {FETCH_SCRIPT}")
    body = "".join(text[start:end])
    assert "def extract_file" in body, "the heredoc is not the extractor"
    out = tmp / "extractor.py"
    out.write_text(body)
    return out


def _raw_rows():
    rows = [r.split("\t") for r in
            (RAW_DIR / "_fetch.tsv").read_text().splitlines()[1:] if r.strip()]
    assert len(rows) == 13, f"expected thirteen raw pages, found {len(rows)}"
    return rows


def test_raw_pages_are_the_bytes_the_manifest_claims():
    """Byte count and digest, so a raw page cannot be edited unnoticed."""

    import hashlib

    main = {r.split("\t")[0]: r.split("\t") for r in
            (REPO_ROOT / "corpora" / "us" / "_manifest.tsv")
            .read_text().splitlines()[1:] if r.strip()}
    for name, url, _at, size, digest, extracts_to in _raw_rows():
        raw = (RAW_DIR / name).read_bytes()
        assert len(raw) == int(size), name
        assert hashlib.sha256(raw).hexdigest() == digest, name
        # And the two manifests agree about how big the page was.
        assert main[extracts_to][4] == size, name


def test_raw_html_reextracts_to_the_stored_corpus(tmp_path):
    """Every stored document, re-derived from the page it came from.

    Byte-for-byte, through the fetch script's own extractor. A single differing
    byte fails: the corpus is either what the extractor makes of those pages or
    it is something nobody can account for.
    """

    import shutil

    extractor = _script_extractor(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    checked = 0
    for name, _url, _at, _size, _digest, extracts_to in _raw_rows():
        copy = work / name
        shutil.copy(RAW_DIR / name, copy)
        subprocess.run([sys.executable, str(extractor), str(copy)],
                       check=True, capture_output=True)
        stored = REPO_ROOT / "corpora" / "us" / extracts_to
        assert copy.read_bytes() == stored.read_bytes(), (
            f"{name} does not re-extract to {extracts_to}"
        )
        checked += 1
    assert checked == 13


def test_the_raw_pages_are_invisible_to_every_corpus_reader():
    """Underscore-prefixed, and a directory, so both filters exclude them."""

    assert RAW_DIR.name.startswith("_")
    assert [p.name for p in _corpus_documents() if p.name.endswith(".htm")] == []


def _master_sets(lexicon):
    m = SecurityMaster(lexicon=lexicon)
    m.load_sec_tickers(str(REPO_ROOT / "master" / "us.json"), market="US")
    return set(m.names), set(m.tickers)


def test_the_lexicon_move_changed_no_master_entry():
    """Set equality, not equal counts.

    Equal cardinality is consistent with a filter that swapped one entry for
    another, and with a filter that never ran at all. What is asserted here is
    that the symmetric difference is empty in both directions, and
    `test_a_lexicon_row_removes_exactly_its_own_entry` is what shows the filter
    is running whilst the difference is empty.
    """

    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    registered = _master_sets(frozenset(reg.lexicon))
    seeded = _master_sets(SEED_LEXICON)
    assert registered[0] ^ seeded[0] == set()
    assert registered[1] ^ seeded[1] == set()


def test_a_lexicon_row_removes_exactly_its_own_entry():
    """The filter fires, and reaches no further than the row that fired it.

    Two probes because the loader consults the lexicon at two points and they
    answer different questions: a ticker is dropped from the ticker set, and a
    name variant is dropped from the name set whilst its longer variants stay.
    `apple` goes and `apple inc.` remains, which is the behaviour a one-word
    issuer name that is also an ordinary word depends on.
    """

    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    base = frozenset(reg.lexicon)
    names, tickers = _master_sets(base)
    assert "aapl" in tickers and "apple" in names and "apple inc." in names

    n1, t1 = _master_sets(base | {"aapl"})
    assert tickers - t1 == {"aapl"} and t1 - tickers == set()
    assert n1 ^ names == set()

    n2, t2 = _master_sets(base | {"apple"})
    assert names - n2 == {"apple"} and n2 - names == set()
    assert "apple inc." in n2
    assert t2 ^ tickers == set()


CONTROL_ARM_FIELDS = (
    "control_arm_delta",
    "control_arm_n_min",
    "control_arm_ratio",
    "control_arm_seed",
)


def _control_arm_under(commit: str, blob: bytes, tmp: Path) -> dict:
    """The four control-arm values, read under the dataclass of ``commit``.

    Read the same way the hash is recomputed, and for the same reason: a field
    read under today's schema is a field read from a different object.
    """

    if commit == "current":
        reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
        return {f: getattr(reg, f) for f in CONTROL_ARM_FIELDS}
    work = tmp / ("ca-" + commit)
    work.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", commit, "src"],
        check=True, capture_output=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(work)], input=tar, check=True)
    (work / "r.json").write_bytes(blob)
    out = subprocess.run(
        [sys.executable, "-c",
         "import json;from fntn.scanner.params import Registration;"
         "r=Registration.load('r.json');"
         "print(json.dumps({f:getattr(r,f) for f in %r}))" % (CONTROL_ARM_FIELDS,)],
        cwd=work, check=True, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    return json.loads(out.stdout)


def test_control_arm_values_unchanged_across_restamps(tmp_path):
    """The claim rows 19 and 20 make, checked against the objects themselves.

    Those rows say the commitment has not moved and that every re-stamp so far
    was caused by some other field. That is the load-bearing sentence in the
    whole chain: a new hash on an unmoved commitment is bookkeeping, and a new
    hash on a moved one is a kill criterion rewritten after the fact. It was
    prose until this test, and prose is what a reader has to take on trust.

    A row is permitted to move exactly the value it names as its causing field,
    and nothing else. No row names one of these four, so today every pair must
    match on all four; the exception is written rather than assumed so that a
    future re-stamp of delta or n_min is legible instead of failing here as if
    it were a defect.
    """

    rows = _history_rows()
    assert len(rows) >= 2, "a chain of one has no pair to compare"
    values = [_control_arm_under(r["commit"], _row_object(r, tmp_path), tmp_path)
              for r in rows]
    pairs = 0
    for older, newer, row in zip(values, values[1:], rows[1:]):
        allowed = row["field"].strip("`")
        for f in CONTROL_ARM_FIELDS:
            if f == allowed:
                continue
            assert older[f] == newer[f], (
                f"row {row['n']} ({row['hash']}) moved {f} from {older[f]} to "
                f"{newer[f]} whilst naming {allowed!r} as its causing field. "
                "Either the causing field is wrong or the commitment moved."
            )
        pairs += 1
    assert pairs == len(rows) - 1


# ---------------------------------------------------------------------------
# §0.5's provenance vocabulary, and the classifications that must stay total.
# ---------------------------------------------------------------------------


def test_every_provenance_tag_is_classified():
    """A tag the classifications have never heard of is a tag read as harmless.

    Before this, the freeze-blocking decision was `tag == "recollection"`, a
    blacklist of one. Adding `reconstructed_hash_verified` to the vocabulary
    under that arrangement would have made it silently benign at every consumer
    at once. Both classifications are asserted total here so that the next tag
    cannot land unclassified.
    """

    assert len(list(Provenance)) == 6, "the vocabulary is not what this checks"
    for tag in Provenance:
        assert isinstance(tag.counts_as_verified, bool), tag
        assert isinstance(tag.blocks_freeze_signature, bool), tag
        # And no tag is both: the signature cannot stand on what it blocks.
        assert not (tag.counts_as_verified and tag.blocks_freeze_signature), tag


def test_reconstructed_is_verified_of_a_kind_and_still_blocks_the_signature():
    """The predicate has two halves and the classification reflects both.

    It reproduces the original hash, so it is not recollection. It is not the
    original artefact, so the signature cannot stand on it.
    """

    p = Provenance.RECONSTRUCTED_HASH_VERIFIED
    assert p.blocks_freeze_signature
    assert not p.counts_as_verified
    assert Provenance.RECOLLECTION.blocks_freeze_signature
    assert not Provenance.VERIFIED_PRIMARY.blocks_freeze_signature
    assert not Provenance.AGENT_GENERATED.blocks_freeze_signature


def test_the_freeze_linter_reads_the_new_tag_rather_than_ignoring_it():
    """The intake refusal fires on it, and the summary names the tag it found.

    The §8 summary is rendered from the record's own fields, so a refusal
    caused by `reconstructed_hash_verified` may not describe itself as
    recollection.
    """

    ctx = intake_ctx(clean_proposal())
    ctx.claim_provenance = {
        "claimed_effect": Provenance.RECONSTRUCTED_HASH_VERIFIED.value
    }
    outcome = run_intake(ctx)
    assert not outcome.passed
    refusal = [r for r in outcome.refusals
               if r.code == "claim_provenance_recollection"]
    assert refusal, [r.code for r in outcome.refusals]
    assert "reconstructed_hash_verified" in refusal[0].summary
    assert "carried recollection provenance" not in refusal[0].summary


def test_an_unknown_provenance_tag_is_refused_rather_than_passed():
    """A tag outside the vocabulary is a claim nothing can classify."""

    ctx = intake_ctx(clean_proposal())
    ctx.claim_provenance = {"claimed_effect": "vibes"}
    with pytest.raises(ValueError):
        run_intake(ctx)


def test_reconstructed_provenance_does_not_make_an_intake_quantified():
    record = make_record()
    record.claimed_effect = "230 bps"
    record.claimed_horizon_sessions = 5
    record.claims = {
        k: ClaimField(k, "v", Provenance.RECONSTRUCTED_HASH_VERIFIED)
        for k in ("claimed_effect", "claimed_horizon_sessions", "measured_on")
    }
    assert record.compute_evidence_tier() is EvidenceTier.POINTER
    # The same record with verified tags IS quantified, so the assertion above
    # is about the tag and not about some other gap in the record.
    record.claims = {
        k: ClaimField(k, "v", Provenance.VERIFIED_PRIMARY)
        for k in ("claimed_effect", "claimed_horizon_sessions", "measured_on")
    }
    assert record.compute_evidence_tier() is EvidenceTier.QUANTIFIED


def test_row_one_is_tagged_reconstructed_and_the_rest_are_not():
    """The tag is on the row whose artefact is gone, and only that row.

    Its predicate's second half, that the reconstruction reproduces the hash
    under the dataclass of the naming commit, is asserted by
    test_registration_history_recomputes. Its first half, that no commit
    carries the artefact, is asserted here: a row tagged reconstructed may not
    also claim a git object.
    """

    tag = Provenance.RECONSTRUCTED_HASH_VERIFIED.value
    tagged = [r for r in _history_rows() if r["provenance"].strip("`") == tag]
    assert len(tagged) == 1 and tagged[0]["hash"] == "890a80e3a8566837"
    assert "git show" not in tagged[0]["object"]
    for row in _history_rows():
        cell = row["provenance"].strip("`")
        assert cell in {t.value for t in Provenance}, row
        if row["hash"] != tagged[0]["hash"]:
            assert cell == Provenance.VERIFIED_PRIMARY.value, row
            assert "git show" in row["object"] or row["commit"] == "current", row


# ---------------------------------------------------------------------------
# Load-time verification, and the third state.
# ---------------------------------------------------------------------------


def test_the_registration_in_the_tree_verifies():
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.hash_verification == Registration.VERIFIED
    assert reg.registered_schema == Registration.schema_fingerprint()


def test_a_tampered_registration_is_refused_not_read(tmp_path):
    """Comparable, and unequal. That is a wrong file, not an old one."""

    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir()
    _complete_registration().save(p)
    raw = json.loads(p.read_text())
    raw["control_arm_delta"] = 40.0          # the kill criterion, edited by hand
    p.write_text(json.dumps(raw))
    with pytest.raises(RegistrationHashMismatch, match="records its hash as"):
        Registration.load(p)


def test_a_schema_change_reports_that_it_cannot_verify_rather_than_verifying(tmp_path):
    """The state that had to exist.

    A recomputation under a different shape answers a different question, so
    its disagreement means nothing. The file loads, and `verified` is not what
    it says.
    """

    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir()
    _complete_registration().save(p)
    raw = json.loads(p.read_text())
    raw["registered_schema"] = "0000000000000000"   # stamped under another shape
    p.write_text(json.dumps(raw))
    reg = Registration.load(p)
    assert reg.hash_verification == Registration.UNVERIFIABLE
    assert reg.hash_verification != Registration.VERIFIED
    assert Registration.UNVERIFIABLE in reg.render()


def test_a_file_predating_the_field_loads_and_claims_nothing(tmp_path):
    """Every registration written before this landed, including the history's."""

    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir()
    _complete_registration().save(p)
    raw = json.loads(p.read_text())
    raw.pop("registered_schema")
    p.write_text(json.dumps(raw))
    assert Registration.load(p).hash_verification == Registration.UNVERIFIABLE

    raw.pop("registered_hash")
    p.write_text(json.dumps(raw))
    assert Registration.load(p).hash_verification == Registration.UNSTAMPED


def test_a_provenance_field_moves_neither_the_hash_nor_the_fingerprint():
    """Which is what makes this landable without a re-stamp.

    `registered_hash`, `registered_schema` and `rationale` are all outside the
    hashed payload, and the fingerprint describes that payload, so a fourth one
    would change neither. A field that reached the payload would change both,
    which is the behaviour §13 rows 19 and 20 depend on.
    """

    a = _complete_registration()
    b = _complete_registration()
    b.registered_hash, b.registered_schema, b.rationale = "x", "y", "z"
    assert a.hash() == b.hash()
    assert Registration.schema_fingerprint() == Registration.schema_fingerprint()


def test_the_fingerprint_moves_when_the_hashed_shape_moves():
    """Otherwise it cannot tell an old file from a wrong one, which is its job."""

    excluded = {"rationale", "registered_hash", "registered_schema"}
    hashed = {f.name for f in dataclasses.fields(Registration)} - excluded
    assert "control_arm_delta" in hashed and "lexicon" in hashed
    # Recomputed from the same inputs the method reads, with one name added.
    import hashlib as _h

    def fingerprint_of(names):
        shape = {
            "registration": sorted(names),
            "corpus": sorted(f.name for f in dataclasses.fields(RegCorpus)),
            "discoverable_class": sorted(
                f.name for f in dataclasses.fields(DiscoverableClass)),
        }
        return _h.sha256(json.dumps(shape, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()[:16]

    assert fingerprint_of(hashed) == Registration.schema_fingerprint()
    assert fingerprint_of(hashed | {"a_new_gate"}) != Registration.schema_fingerprint()


# ---------------------------------------------------------------------------
# §13 rows 21a and 21b: the ratification harness.
# ---------------------------------------------------------------------------

from fntn.scanner import ratify
from fntn.scanner.ratify import Agreement, RatificationRefused


def _labelled():
    subjects = load_labelled(str(REPO_ROOT / "docs" / "labelled_proposals.json"))
    assert len(subjects) == 42
    return subjects


def test_the_draw_comes_from_the_registered_seed_and_nowhere_else():
    """Unchoosable by whoever runs it, and replayable from the registration.

    A ratification sample the runner can steer is a sample chosen after the
    labels are known, whatever order the two actually happened in.
    """

    subjects = _labelled()
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    a = [l.subject_id for l in ratify.draw(subjects, reg.control_arm_seed)]
    b = [l.subject_id for l in ratify.draw(subjects, reg.control_arm_seed)]
    assert len(a) == ratify.DRAW_N == 12
    assert a == b
    # A different registration draws a different twelve, so a re-draw costs a
    # re-stamp with the causing field named.
    assert a != [l.subject_id for l in ratify.draw(subjects, reg.control_arm_seed + 1)]


def test_the_draw_does_not_share_a_stream_with_the_control_arm():
    """Same registered seed, two purposes, and the salt keeps them apart."""

    import random

    subjects = _labelled()
    drawn = sorted([l for l in subjects if not l.probe_route],
                   key=lambda l: l.subject_id)
    assert len(drawn) == 36
    unsalted = random.Random(20260826).sample(drawn, 12)
    salted = ratify.draw(subjects, 20260826)
    assert [l.subject_id for l in salted] != [l.subject_id for l in unsalted]


def test_the_worksheet_withholds_the_drawn_arm_labels_and_shows_every_probe():
    """The withholding is the design, so it is asserted rather than assumed."""

    subjects = _labelled()
    text = ratify.render_draw(subjects, 20260826, "testhash", date(2026, 8, 27))
    body = text.split("## Drawn arm")[1].split("## Authored probes")[0]
    for l in ratify.draw(subjects, 20260826):
        assert f"`{l.subject_id}`" in body
        # The only occurrences of the taxonomy's words in this half are the
        # operator's own empty box.
    assert body.count("class_level") == body.count(
        "operator_label (class_level / not_class_level):") * 2
    assert "clerk label" not in body

    probes = text.split("## Authored probes")[1]
    for l in [x for x in subjects if x.probe_route]:
        assert f"`{l.subject_id}`" in probes
        assert l.probe_route in probes
    assert probes.count("clerk label") == 6


def test_the_refutation_rule_is_written_before_any_label_is_revealed():
    text = ratify.render_draw(_labelled(), 20260826, "h", date(2026, 8, 27))
    assert "one disagreement in twelve refutes the clerk's labels for the whole" in text.lower()
    # And it is above the subjects, not in a footnote after them.
    assert text.index("refutes the clerk's labels") < text.index("## Drawn arm")


def test_one_disagreement_refutes_the_whole_arm():
    subjects = _labelled()
    picked = ratify.draw(subjects, 20260826)
    labels = {l.subject_id: l.is_class_level for l in picked}
    agreed = ratify.reveal(subjects, 20260826, labels)
    assert not agreed.refutes and agreed.agreed == 12
    assert "NOT REFUTED" in agreed.render()

    labels[picked[0].subject_id] = not picked[0].is_class_level
    refuted = ratify.reveal(subjects, 20260826, labels)
    assert refuted.refutes
    assert refuted.agreed == 11
    out = refuted.render()
    assert "REFUTED" in out and "FOR THE WHOLE DRAWN" in out
    assert "roughly 3 across it" in out


def test_a_blank_label_is_neither_agreement_nor_disagreement():
    subjects = _labelled()
    picked = ratify.draw(subjects, 20260826)
    labels = {l.subject_id: l.is_class_level for l in picked[1:]}
    with pytest.raises(RatificationRefused, match="no operator label for"):
        ratify.reveal(subjects, 20260826, labels)


def test_the_harness_refuses_a_draw_larger_than_the_arm():
    with pytest.raises(RatificationRefused, match="Refusing to shrink"):
        ratify.draw(_labelled(), 20260826, n=99)


def test_neither_reveal_reports_a_rate():
    """Counts with their own denominator, and no percentage anywhere."""

    subjects = _labelled()
    picked = ratify.draw(subjects, 20260826)
    for labels in (
        {l.subject_id: l.is_class_level for l in picked},
        {l.subject_id: (l.is_class_level if i else not l.is_class_level)
         for i, l in enumerate(picked)},
    ):
        out = ratify.reveal(subjects, 20260826, labels).render()
        assert "%" not in out


def test_the_worksheet_states_the_bound_and_never_the_point_estimate():
    """0 of 36 is a count. The rate it supports is an upper bound near 8.3%."""

    text = ratify.render_draw(_labelled(), 20260826, "h", date(2026, 8, 27))
    assert "upper bound" in text and "8.3%" in text
    assert "0%" not in text


OPEN_ITEMS = REPO_ROOT / "docs" / "OPEN_ITEMS.md"


def _open_items_row(n: str):
    """(status cell, note cell) for a §13 row, so a status is read as a status.

    Split rather than searched: `21b`'s note contains the sentence "PROVISIONAL
    and not BLOCKED", and a substring test over the whole row would read that
    as a status of BLOCKED.
    """

    rows = [l for l in OPEN_ITEMS.read_text().splitlines()
            if l.startswith(f"| {n} |")]
    assert len(rows) == 1, f"expected one row {n}, found {len(rows)}"
    cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    assert len(cells) == 4, cells[:2]
    return cells[2], cells[3]


def test_row_21a_is_blocked_and_states_a_bound_not_a_rate():
    """The split's whole content, locked against drift back to `0%`.

    A point estimate of zero on 36 trials is a precision claim the sample does
    not carry: a fence refusing one clean proposal in twenty produces this
    reading better than one time in six.
    """

    status, note = _open_items_row("21a")
    assert status == "**BLOCKED**"
    assert "upper bound" in note.lower() and "8.3%" in note
    assert "0 of 36" in note          # the count stands
    assert "0 events in 36 trials" in note
    assert "rule of three" in note
    # `0%` appears only where it is being withdrawn, never as the reading.
    assert "It is not 0%" in note
    assert "**0%** previously carried on this row is withdrawn" in note
    assert "refused (0%)" not in note
    # The blocker is named, and it is not labelling effort.
    assert "design segment" in note and "§7.1" in note
    assert "chosen and not derived" in note


def test_row_21b_is_provisional_coverage_and_never_a_rate():
    status, note = _open_items_row("21b")
    assert status == "**PROVISIONAL**"
    assert "5 of 6 routes closed" in note
    assert "never a rate" in note.lower()
    assert "title-case bare ticker" in note
    # No percentage anywhere in the note. Coverage carries no denominator.
    assert "%" not in note
    assert "operator reading the six" in note


def test_the_old_row_21_is_gone_from_both_registers():
    """One row carried two quantities with two blockers and one status."""

    assert not [l for l in OPEN_ITEMS.read_text().splitlines()
                if l.startswith("| 21 |")]
    spec = (REPO_ROOT / "docs" / "spec" / "from_narrative_to_null_v1_14.md").read_text()
    assert "| 21 | **Entity-fence error rates**" not in spec
    assert "| 21a | **Fence false-positive rate" in spec
    assert "| 21b | **Fence false-negative route coverage" in spec


# ---------------------------------------------------------------------------
# The run report (§9.2).
# ---------------------------------------------------------------------------

from fntn.scanner import report as report_mod
from fntn.scanner.report import Draft, RunReport, queue_from_ledger

RANKING_WORDS = (
    "merit", "severity", "priority", "score", "rank", "importance",
    "urgency", "promising", "best", "worst", "recommend",
)


def _report_ledger():
    """A ledger whose every other plausible ordering disagrees with the count.

    Insertion order is B, C, D, A. Identifier order is aaa, bbb, mmm, zzz.
    Class order is a_first, b, m, z_last. Outstanding-count order is A, B, D, C.
    No two of those agree, so the rendered order identifies the key uniquely.
    """

    ledger = Ledger(parameter_hash="report-test")
    spec = [
        # (id, class, outstanding codes, registered_sign)
        ("dir-aaa", "a_first", ["delta_min_absent"], 1),
        ("dir-mmm", "m_third",
         ["delta_min_absent", "premortem_unratified",
          "literature_search_absent"], 1),
        ("dir-bbb", "b_second", ["premortem_unratified"], 1),
        ("dir-zzz", "z_last", [], 1),
    ]
    for did, cls, blockers, sign in spec:
        d = _directive()
        d.directive_id = did
        d.event_class = cls
        d.registered_sign = sign
        ledger.write_directive(d, "blocked_on_operator")
        for code in blockers:
            ledger.write_refusal(summaries.render(code, did, {"directive_id": did}))
    return ledger


def test_the_queue_is_ordered_by_outstanding_count_and_nothing_else():
    """The one design decision in the report, and it is a refusal.

    Any other ordering is this file telling the operator which of their own
    decisions matters most. The fixture is built so that identifier order,
    class order and insertion order each disagree with the count, which is what
    makes the rendered order evidence about the key rather than a coincidence.
    """

    ledger = _report_ledger()
    drafts = queue_from_ledger(ledger)
    assert [d.directive_id for d in drafts] == [
        "dir-zzz",   # 0 outstanding, and last by identifier, class and insertion
        "dir-aaa",   # 1
        "dir-bbb",   # 1, after aaa on the identifier tie-break alone
        "dir-mmm",   # 3
    ]
    assert [d.n_outstanding for d in drafts] == [0, 1, 1, 3]
    ledger.close()


def test_zero_outstanding_drafts_come_first_under_their_own_heading():
    ledger = _report_ledger()
    text = _render(ledger)
    queue = text.split("## 4. The queue")[1].split("## 5.")[0]
    assert "Nothing outstanding: 1 draft(s). **These need a decision now.**" in queue
    assert queue.index("dir-zzz") < queue.index("dir-aaa") < queue.index("dir-mmm")
    ledger.close()


def _render(ledger, **over) -> str:
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    kwargs = dict(
        registration=reg, ledger=ledger, corpora=[("./corpora/us", "abcd")],
        commit="deadbeef", on=date(2026, 8, 27),
    )
    kwargs.update(over)
    return RunReport(**kwargs).render()


def test_the_report_carries_no_ranking_key_other_than_the_count():
    """No merit, no severity, no score, no recency: not in the table, not in the prose.

    A column that ranks does not have to be sorted on to do damage. A reader
    given a `merit` figure beside a draft ranks by it themselves, and the file
    has then made the judgement it declined to make in the sort.
    """

    ledger = _report_ledger()
    queue = _render(ledger).split("## 4. The queue")[1].split("## 5.")[0]

    # A ranking key lives in a column or a heading. Those are checked with no
    # exemption at all.
    structure = "\n".join(
        l for l in queue.splitlines() if l.startswith(("|", "#"))
    ).lower()
    for word in RANKING_WORDS:
        assert word not in structure, word

    # The prose is checked too, less the one sentence that exists to disclaim
    # these words. It is matched verbatim rather than pattern-matched, so
    # rewording it fails this test and sends the next reader back to it.
    disclaimers = (
        "Ties break on the directive identifier, which ranks nothing.",
        "There is no merit column, no severity, no score and no recency: any "
        "of them would be this file telling the operator which of their own "
        "decisions matters most, which is the clerk becoming an analyst.",
    )
    prose = queue
    for d in disclaimers:
        assert d in queue, d
        prose = prose.replace(d, "")
    prose = prose.lower()
    for word in RANKING_WORDS:
        assert word not in prose, word

    # The only numeric column in the waiting table is the outstanding count.
    header = [l for l in queue.splitlines() if l.startswith("| outstanding |")]
    assert header == ["| outstanding | directive | class | awaiting |"]
    ledger.close()


def test_the_queue_ordering_survives_a_reversed_ledger():
    """Same drafts, opposite insertion order, same rendered order."""

    a = [d.directive_id for d in queue_from_ledger(_report_ledger())]
    ledger = Ledger(parameter_hash="report-test")
    for did, cls, blockers in reversed([
        ("dir-aaa", "a_first", ["delta_min_absent"]),
        ("dir-mmm", "m", ["delta_min_absent", "premortem_unratified",
                          "literature_search_absent"]),
        ("dir-bbb", "b", ["premortem_unratified"]),
        ("dir-zzz", "z", []),
    ]):
        d = _directive()
        d.directive_id, d.event_class, d.registered_sign = did, cls, 1
        ledger.write_directive(d, "blocked_on_operator")
        for code in blockers:
            ledger.write_refusal(summaries.render(code, did, {"directive_id": did}))
    assert [d.directive_id for d in queue_from_ledger(ledger)] == a
    ledger.close()


def test_the_report_has_its_eight_sections_in_order():
    ledger = _report_ledger()
    text = _render(ledger)
    wanted = [
        "## 1. Provenance",
        "## 2. Intake funnel",
        "## 3. Fence report",
        "## 4. The queue",
        "## 5. Control arm",
        "## 6. Reason-code coverage",
        "## 7. Refutations",
        "## 8. Not measured",
    ]
    positions = [text.index(w) for w in wanted]
    assert positions == sorted(positions)
    ledger.close()


def test_the_provenance_header_carries_the_fingerprint_and_its_verdict():
    ledger = _report_ledger()
    prov = _render(ledger).split("## 1. Provenance")[1].split("## 2.")[0]
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.hash() in prov
    assert reg.registered_schema in prov
    assert reg.hash_verification in prov
    assert "deadbeef" in prov and "abcd" in prov
    ledger.close()


def test_the_two_fence_arms_are_reported_apart_and_neither_is_rounded_up():
    ledger = _report_ledger()
    fences = _render(ledger).split("## 3. Fence report")[1].split("## 4.")[0]
    assert "upper bound" in fences and "8.3%" in fences
    assert "5 of 6 routes closed" in fences
    assert "coverage, never a rate" in fences
    assert "is not 0%" in fences
    # The probe arm's line carries no percentage.
    probe_line = [l for l in fences.splitlines() if "authored probes (21b)" in l]
    assert len(probe_line) == 1 and "%" not in probe_line[0]
    ledger.close()


def test_the_control_arm_verdict_is_not_yet_run_and_not_undetermined():
    """`undetermined_at_budget` would say a measurement had happened."""

    ledger = _report_ledger()
    arm = _render(ledger).split("## 5. Control arm")[1].split("## 6.")[0]
    assert "**NOT YET RUN**" in arm
    assert "undetermined_at_budget" in arm and "claiming" in arm
    assert "not measured" in arm
    ledger.close()


def test_the_budget_count_is_printed_even_at_zero_and_never_inside_row_23():
    ledger = _report_ledger()
    zero = _render(ledger)
    assert "abandoned to intake budget: **0**" in zero

    some = _render(ledger, budget_abandoned=3)
    dist = some.split("### Abort-position distribution")[1].split("### Intake points")[0]
    assert "Beside this distribution and not inside it" in dist
    assert "3 subject(s) abandoned to the intake budget" in dist
    # And it is not added into any position's count.
    assert "| 3 | `proposal_names_entity` | 0 |" in dist
    ledger.close()


def test_unexercised_intake_points_are_named_not_counted():
    ledger = _report_ledger()
    section = _render(ledger).split("### Intake points not exercised")[1].split("## 3.")[0]
    for code in codes.INTAKE_ORDER:
        assert f"`{code}`" in section
    ledger.close()


def test_the_refutations_section_is_seeded_with_the_three_to_date():
    ledger = _report_ledger()
    ref = _render(ledger).split("## 7. Refutations")[1].split("## 8.")[0]
    assert "94%" in ref
    assert "Trust Holdings and Transactions" in ref
    assert "RAW FETCHED PAGES WERE NEVER RETAINED" in ref
    assert len(report_mod.STANDING_REFUTATIONS) == 3
    ledger.close()


def test_a_report_never_overwrites_another(tmp_path):
    """Append-only, one file per run."""

    on = date(2026, 8, 27)
    first = report_mod.next_path(tmp_path, on)
    first.write_text("x")
    second = report_mod.next_path(tmp_path, on)
    assert second != first and not second.exists()
    second.write_text("y")
    assert report_mod.next_path(tmp_path, on).name.endswith("_03.md")
    assert first.read_text() == "x"


def test_a_corpus_with_no_manifest_is_not_reported_as_clean(tmp_path):
    got = report_mod.corpus_digest([str(tmp_path)])
    assert "no manifest" in got[0][1]


# ---------------------------------------------------------------------------
# The intake budget (§13 row 27).
#
# The decision is taken once, at capture. Everything below exists to hold that
# line: a clock in the replay path makes rule 1 false, because the same inputs
# would then produce a different refusal set on a different machine.
# ---------------------------------------------------------------------------


def _exploding_clock():
    def clock():
        raise AssertionError(
            "a replay called a clock. The decision was taken at capture and "
            "the ledger holds it; re-racing it makes the run's refusal set "
            "depend on the machine it was replayed on."
        )
    return clock


def _capture(clock_step: float, subject_budget: float = 120.0):
    budget = MeasuringBudget(
        point_budget_s=20.0,
        subject_budget_s=subject_budget,
        retry_max=1,
        clock=itertools.count(0.0, clock_step).__next__,
    )
    outcome = intake_runner(budget=budget).run(
        "s1", intake_ctx(clean_proposal()), mode=Mode.FULL_PANEL
    )
    return outcome, budget


def test_a_slow_point_abandons_the_subject_after_its_retry():
    outcome, budget = _capture(30.0)
    assert outcome.budget_exhausted
    assert not outcome.passed
    assert [r.code for r in outcome.refusals] == ["intake_budget_exhausted"]
    # Two attempts: the over-run, then the one retry the registration allows.
    exhausted = [d for d in budget.decisions if d.exhausted]
    assert exhausted[0].attempts == 2
    assert exhausted[0].budget_s == 20.0


def test_a_budget_abandonment_is_not_an_abort_position():
    """§13 row 23 counts where a subject FAILED, and this did not fail a check.

    Recording it as a position would put a clock's verdict in a check's column,
    and row 23's distribution is a calibration.
    """

    outcome, _ = _capture(30.0)
    assert outcome.budget_exhausted
    assert outcome.failed_at_position is None


def test_a_fast_run_is_not_charged_and_nothing_is_abandoned():
    outcome, budget = _capture(0.5)
    assert not outcome.budget_exhausted
    assert all(not d.exhausted for d in budget.decisions)
    assert all(d.attempts == 1 for d in budget.decisions if d.point != "__subject__")


def test_the_subject_budget_bites_where_every_point_is_inside_its_own():
    """Twelve comfortable points still add to an intake nobody would run."""

    outcome, budget = _capture(15.0, subject_budget=40.0)
    assert outcome.budget_exhausted
    charged = [d for d in budget.decisions if d.exhausted]
    assert charged and charged[-1].point == "__subject__"
    assert charged[-1].budget_s == 40.0


def test_a_replay_under_a_different_wall_clock_reproduces_the_decision(tmp_path):
    """THE test for this feature. Byte-for-byte, including the timestamp.

    Capture races a clock once. Replay is given the recorded decisions and a
    clock that raises if it is touched, and must produce an identical refusal:
    same code, same fields, same rendered summary, same `attempted_at`. If any
    of those moved, the run would not be replayable from the parameter hash and
    rule 1 would be false.
    """

    outcome, budget = _capture(30.0)
    assert outcome.budget_exhausted

    # Through the ledger, as production would: the records are written and read
    # back rather than passed in memory.
    ledger = Ledger(parameter_hash="budget-replay")
    ledger.write_budget_decisions(budget.decisions)
    rows = ledger.budget_decisions("s1")
    assert rows, "the ledger recorded no budget decision to replay"

    replay = ReplayedBudget(decisions_from_rows(rows))
    replay.clock = _exploding_clock()          # touched, and the test fails
    replayed = intake_runner(budget=replay).run(
        "s1", intake_ctx(clean_proposal()), mode=Mode.FULL_PANEL
    )

    def serialise(o):
        return json.dumps(
            [
                {
                    "code": r.code,
                    "subject_id": r.subject_id,
                    "surface": r.surface,
                    "fields": r.fields,
                    "summary": r.summary,
                }
                for r in o.refusals
            ],
            sort_keys=True,
        )

    assert serialise(replayed) == serialise(outcome)
    assert replayed.budget_exhausted == outcome.budget_exhausted
    assert replayed.failed_at_position == outcome.failed_at_position
    ledger.close()


def test_the_replay_budget_holds_no_clock_at_all():
    """Not "does not call one": has none to call."""

    replay = ReplayedBudget([])
    assert not hasattr(replay, "clock")
    assert replay.replaying is True
    assert MeasuringBudget(1.0, 2.0).replaying is False


def test_a_replay_missing_a_record_refuses_rather_than_re_timing():
    replay = ReplayedBudget([])
    with pytest.raises(BudgetReplayError, match="a replay that measures is not a replay"):
        replay.run_point("s1", "agent_overreached_schema", lambda: None)


def test_the_ledger_records_elapsed_the_budget_and_the_decision():
    outcome, budget = _capture(30.0)
    ledger = Ledger(parameter_hash="b")
    ledger.write_budget_decisions(budget.decisions)
    rows = ledger.budget_decisions()
    assert rows
    for row in rows:
        assert set(row) == {
            "subject_id", "point", "elapsed_s", "budget_s", "attempts",
            "exhausted", "at",
        }
    assert ledger.budget_abandoned() == 1
    assert Ledger(parameter_hash="b").budget_abandoned() == 0
    ledger.close()


def test_the_budget_is_registered_and_reaches_the_hash():
    a = _complete_registration()
    for field_name, value in (
        ("intake_point_budget_s", 30.0),
        ("intake_subject_budget_s", 200.0),
        ("budget_retry_max", 2),
    ):
        b = _complete_registration(**{field_name: value})
        assert a.hash() != b.hash(), field_name
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.intake_point_budget_s == 20.0
    assert reg.intake_subject_budget_s == 120.0
    assert reg.budget_retry_max == 1


def test_a_ceiling_of_zero_is_refused_as_a_refusal_of_the_whole_surface():
    assert any("must exceed zero (§13 row 27)" in g
               for g in _complete_registration(intake_point_budget_s=0).missing())
    assert any("may not be given less time" in g
               for g in _complete_registration(intake_subject_budget_s=5.0).missing())
    assert any("budget_retry_max" in g
               for g in _complete_registration(budget_retry_max=-1).missing())


def test_the_budget_code_is_non_positional_and_says_why():
    rc = codes.ALL_CODES["intake_budget_exhausted"]
    assert rc.refuse_to_score
    assert rc.code not in codes.INTAKE_ORDER
    assert rc.code in codes.INTAKE_NON_POSITIONAL
    # The resurrection predicate names both routes back, and both are checkable.
    assert "budget has been raised" in rc.resurrection
    assert "later attempt" in rc.resurrection


def test_the_budget_summary_renders_from_the_records_own_fields():
    outcome, _ = _capture(30.0)
    summary = outcome.refusals[0].summary
    assert "against a registered budget of 20.000s" in summary
    assert "on attempt 2" in summary
    assert "a replay reads this figure and does not re-time the work" in summary
