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
import hashlib
import itertools
import json
import os
import re
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
    UNCLASSIFIED,
    ControlArmVerdict,
    draw_control_mechanisms,
    prompt_sha,
    proposal_schema,
    schema_sha,
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
    # Two non-positional codes, for two different reasons, and the set is
    # asserted exhaustively so a third cannot arrive quietly.
    # `intake_budget_exhausted`: a ceiling on time is an interruption and not a
    # thirteenth check. `agent_payload_off_schema`: the element never became a
    # proposal, so it never entered intake and has no position at which it
    # could have aborted. Either given a position would land in §13 row 23's
    # distribution as a check that refused.
    assert codes.INTAKE_NON_POSITIONAL == {
        "intake_budget_exhausted",
        "agent_payload_off_schema",
        "agent_payload_not_a_list",
    }
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
            registered_sign=1,
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
            registered_sign=1,
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
        # §7.2's fraction is registered from 27 Aug 2026 and ScanConfig no
        # longer defaults it, so every caller states it, tests included.
        audit_fraction=0.10,
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
        audit_fraction=0.10,
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


def test_no_ledger_read_path_hands_out_a_directive_without_its_origin():
    """P119: the crossing CLAUDE.md forbids is not an import, so no import fence catches it.

    `CLAUDE.md`: agent-origin material may not enter the §3.5 item pipeline, or
    §7.1's headline is re-based on an agent-selected population.
    `assert_import_fence` and `assert_reverse_import_fence` between them cover
    module imports in both directions. **They cannot cover this one**, because
    the discovery layer and the item pipeline share a ledger: the crossing is a
    SELECT, and a SELECT is not an import.

    The hole found by looking: `queue_from_ledger` selected `directive_id`,
    `event_class`, `delta_min`, `registered_sign` and `registered_at`, and NOT
    `origin`. Every consumer built on it therefore received a directive list
    with the marker already stripped, and the §3.5 prohibition is unenforceable
    at the point where the information is gone. That is the same shape as the
    underscore-directory hole: the rule was right and the read path walked
    round it.

    This test is the fence for the ledger direction. Any function returning a
    directive out of the ledger must carry its origin, so that a consumer can
    refuse agent material rather than being unable to see it.
    """

    ledger = Ledger(parameter_hash="origin-fence")
    for did, origin in (("dir-agent", Origin.AGENT),
                        ("dir-operator", Origin.OPERATOR),
                        ("dir-control", Origin.RANDOM_CONTROL)):
        d = _directive(origin=origin)
        d.directive_id = did
        ledger.write_directive(d, "blocked_on_operator")

    drafts = {d.directive_id: d for d in queue_from_ledger(ledger)}
    assert set(drafts) == {"dir-agent", "dir-operator", "dir-control"}

    # Every draft names its origin, and the agent one is identifiable as such.
    for did, expected in (("dir-agent", "agent"),
                          ("dir-operator", "operator"),
                          ("dir-control", "random_control")):
        assert drafts[did].origin == expected, (
            f"{did} came out of the ledger without its origin; a consumer "
            "cannot refuse what it cannot see"
        )

    # And the discovery-origin set is nameable in one place rather than by
    # each consumer inventing its own test.
    assert drafts["dir-agent"].is_discovery_origin
    assert not drafts["dir-operator"].is_discovery_origin
    ledger.close()


def test_the_import_fence_now_runs_in_both_directions(monkeypatch):
    """P115: the existing fence covered one direction of a two-way prohibition.

    `assert_import_fence` stops `discovery.py` reaching prices, outcomes and
    gates, so selection cannot see evaluation. Nothing stopped the reverse, and
    the reverse is the prohibition CLAUDE.md states in its own words: agent
    origin material may not enter the §3.5 item pipeline, because it would
    re-base §7.1's headline on an agent-selected population.

    ***The answer moved from NOT_APPLICABLE to CLEAN on 27 August 2026, and
    that is the fence starting to work rather than a test being relaxed.***
    Until then no forbidden module existed, so the walk had nothing to walk and
    a not-applicable check may never be read as a pass. **`fntn.data` now
    exists**, holding the delisting register, and it is in that package rather
    than under `fntn.scanner` *precisely so this fence has a name to match*: a
    delisting is an OUTCOME, and a register of outcomes reachable from
    `discovery.py` is the contamination §3.7 exists against.

    So the walk is real: it imports `fntn.data`, computes its closure, and
    establishes that the closure does not reach the discovery layer.
    """

    from fntn.scanner.fences import (
        ImportFenceBreach,
        ReverseImportFenceState,
        assert_reverse_import_fence,
    )

    # A real closure is now walked, and it is clean.
    assert assert_reverse_import_fence() is ReverseImportFenceState.CLEAN

    # And when a forbidden module DOES exist and reaches the discovery layer,
    # the fence refuses. Built rather than waited for, because a fence first
    # exercised by the breach it exists against is a fence nobody has tested.
    import sys
    import types

    breaching = types.ModuleType("fntn.gates")
    breaching.__file__ = "<synthetic>"
    breaching.discovery = __import__("fntn.scanner.discovery", fromlist=["x"])
    monkeypatch.setitem(sys.modules, "fntn.gates", breaching)
    with pytest.raises(ImportFenceBreach) as caught:
        assert_reverse_import_fence()
    assert "may not enter the §3.5 item pipeline" in str(caught.value)


def test_a_sweep_refuses_over_a_corpus_that_is_not_committed(tmp_path):
    """P114: the invariant against a fourth instance of one class.

    Three times now a thing this project depended on turned out not to be
    retrievable: the raw fetched pages were never retained, the object behind
    `890a80e3a8566837` survives only as a reconstruction, and the corpus the
    twelve queued drafts were swept from is in no commit at all. Each was
    closed as an instance. The class stayed open.

    The class is: **material that decided something was not committed at the
    moment it decided it.** The invariant is the only closure that addresses
    the class rather than an instance -- a sweep may not read a corpus that git
    cannot produce again.

    Written to fail first, against a corpus directory that exists on disk and
    in no commit.
    """

    from fntn.scanner.corpusio import uncommitted_routes

    loose = tmp_path / "corpora" / "loose"
    loose.mkdir(parents=True)
    (loose / "doc.txt").write_text("a document nothing can retrieve again")

    problems = uncommitted_routes([str(loose)])
    assert problems, "an uncommitted corpus must be reported, not swept"
    route, reason = problems[0]
    assert str(loose) in route
    # The reason names WHICH failure, because "not committed" spans three very
    # different states and a reader must not have to guess which.
    assert "not a git" in reason or "untracked" in reason or "modified" in reason

    # And the committed corpus in this very tree passes, so the check is
    # discriminating rather than merely strict.
    assert uncommitted_routes(["./corpora/us"]) == []


def test_a_sweep_refuses_when_the_audit_fraction_is_unregistered():
    """§7.2's fraction has one source, and an unset one is a refusal (P112).

    It was a default on ScanConfig and a default again in ingest.py, and the
    registration carried it in neither place, so two sweeps under one parameter
    hash could audit different fractions and nothing on the record would say
    which. Every attribution statistic in §7.2 computes on the audit sample
    exclusively, so that is not a cosmetic gap.

    The repair is the field, and this test is what stops the silent path being
    left open beside the registered one: a ScanConfig that never received a
    fraction must refuse rather than reach for 0.10.
    """

    ledger = Ledger(parameter_hash="unset-audit")
    config = ScanConfig(parameter_hash="unset-audit", entity_fence=FENCE)
    assert config.audit_fraction is None

    with pytest.raises(ValueError) as caught:
        scan(
            StubClient([{}]),
            [Corpus("c1", Partition.EXTERNAL, ["doc"])],
            [GridCell("insider_dealing", "drawn population", "a drawn mechanism")],
            config,
            ledger,
            now=NOW,
        )
    assert "audit_fraction is unset" in str(caught.value)
    # And it says WHY, not merely that: a refusal whose reason a reader has to
    # infer is the kind this project keeps refusing to write.
    assert "attribution statistic" in str(caught.value)


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

    # -- the loader, through a REAL scan over a payload the schema does not
    # describe (B16). Written as a scan and not as a direct `render` call
    # because the defect it covers was a crash in the path between the model's
    # reply and the funnel, and a hand-written refusal would exercise the
    # template whilst leaving that path exactly as it was.
    from fntn.scanner.discovery import Corpus as _SwCorpus, GridCell as _Cell
    from fntn.scanner.run import ScanConfig as _Cfg, scan as _scan

    class _OffSchemaClient:
        _replies = [
            {"proposals": ["a bare string where an object was required"]},
            # The shape two of three families actually returned on the first
            # live sweep: `proposals` as a JSON string, not an array.
            {"proposals": "[{\"event_definition\": \"...\"}]"},
        ]

        def __init__(self):
            self._n = 0

        def complete(self, system, user, schema):
            reply = self._replies[min(self._n, len(self._replies) - 1)]
            self._n += 1
            return reply

    _off_ledger = Ledger(parameter_hash="coverage-offschema")
    _res = _scan(
        _OffSchemaClient(),
        [_SwCorpus("c-off", Partition.EXTERNAL, ["doc-1"]),
         _SwCorpus("c-notalist", Partition.EXTERNAL, ["doc-2"])],
        [_Cell("insider_dealing", "pop", "a mechanism")],
        _Cfg(parameter_hash="coverage-offschema", audit_fraction=1.0,
             control_arm_ratio=1.0, control_arm_seed=1),
        _off_ledger,
    )
    # It is counted into the denominator, not silently dropped from it.
    assert _res.proposed >= 1
    _emitted = {c for c, _ in _off_ledger.code_distribution()}
    assert "agent_payload_off_schema" in _emitted
    assert "agent_payload_not_a_list" in _emitted, (
        "the real scan did not emit the code; a hand-written refusal would "
        "then be covering a branch nothing reaches"
    )
    ledger.write_refusal(
        summaries.render(
            "agent_payload_off_schema", "prop-offschema-c-off-0",
            {"index": 0, "got": "str", "corpus_id": "c-off",
             "failed_field": "the element itself"},
        )
    )
    ledger.write_refusal(
        summaries.render(
            "agent_payload_not_a_list", "prop-notalist-c-notalist",
            {"corpus_id": "c-notalist", "got": "str", "length": 27,
             "failed_field": "proposals"},
        )
    )
    _off_ledger.close()

    # -- sizing, the derived clip floor (§13 rows 29 and 30) --------------
    # All three fire here rather than in the funnel, because the funnel has no
    # sizing path: the derivation is a calculator that refuses, and a code
    # defined and never emitted is an untested branch whichever surface it is
    # on.
    from fntn.scanner.sizing import FixedCost as _FC, derive_clip_floor as _floor
    ledger.write_refusal(_floor(_FC("US", "USD", 6.00, 0.0), None))
    ledger.write_refusal(_floor(_FC("UK", "GBP", None, None), 10.0))
    ledger.write_refusal(_floor(_FC("UK Main Market", "GBP", 1.00, 61.4), 10.0))

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

    # -- provenance, both ends of the class (P114) -------------------------
    # One refuses to CREATE an unreproducible record; one MARKS one that
    # already is. Neither is reachable from the funnel, which is the point:
    # they are the ledger's own hygiene and they still must be exercised.
    ledger.write_refusal(
        summaries.render(
            "corpus_not_committed",
            "corpus:./corpora/loose",
            {"route": "./corpora/loose",
             "detail": "holds untracked content that no commit carries: doc.txt"},
        )
    )
    ledger.write_refusal(
        summaries.render(
            "population_not_replayable",
            "prop-unreplayable",
            {"subject_id": "prop-unreplayable",
             "parameter_hash": "a06400ef28ebb54c",
             "material": "ASX and ASIC documents"},
        )
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
    SCHEMA_PREFIX,
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
        agent_model="claude-test-0",
        # §13 row 40. Supplied here rather than defaulted on the dataclass, for
        # the reason `agent_model` is: a default is a second copy of a value the
        # hash is supposed to be the only home for.
        agent_prompt_sha=prompt_sha(),
        proposal_schema_sha=schema_sha(),
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
        digest = _h.sha256(json.dumps(shape, sort_keys=True,
                                      separators=(",", ":")).encode()).hexdigest()[:16]
        return SCHEMA_PREFIX + digest

    assert fingerprint_of(hashed) == Registration.schema_fingerprint()
    assert fingerprint_of(hashed | {"a_new_gate"}) != Registration.schema_fingerprint()


# ---------------------------------------------------------------------------
# The fingerprint is typed, so a hash sweep cannot read it as a stamp.
# ---------------------------------------------------------------------------

#: The sweep for registration hashes, as `docs/REGISTRATION_HISTORY.md` states
#: it.  Sixteen hex characters, not preceded by a colon and not part of a longer
#: hex run: the colon is what excludes the digest half of a typed fingerprint.
#: The literal is asserted to be in that document below, so the prose cannot
#: drift from the sweep that is actually run.
HASH_SWEEP = r"(?<![:0-9a-fA-F])[0-9a-f]{16}(?![0-9a-fA-F])"


def test_the_schema_fingerprint_is_typed_and_cannot_be_read_as_a_stamp():
    """It was sixteen hex characters, which is what a registration hash is.

    A sweep of `discovery_registration.json` found two such values and needed a
    person to say which was a stamp.  A check only a person can complete is not
    machine-checkable and by this project's own standard is not a check.
    """

    fp = Registration.schema_fingerprint()
    assert fp.startswith(SCHEMA_PREFIX)
    assert not re.fullmatch(r"[0-9a-f]{16}", fp)
    # The digest survives untouched under the prefix; the prefix types the
    # value and is not part of what the fingerprint asserts.
    assert re.fullmatch(r"[0-9a-f]{16}", fp[len(SCHEMA_PREFIX):])


def test_a_hash_sweep_of_the_registration_finds_only_registration_hashes():
    """The sweep run, not described.

    Every sixteen-hex token the registration file yields must be a hash the
    history document records.  Before the prefix landed this was false by one
    token every time, and the reconciliation of 27 August had to write a
    paragraph explaining that the extra one was not an unrecorded stamp.
    """

    text = (REPO_ROOT / REGISTRATION_FILE).read_text()
    found = set(re.findall(HASH_SWEEP, text))
    recorded = set(re.findall(r"[0-9a-f]{16}", HISTORY_MD.read_text()))
    assert found, "the sweep found nothing, so it is not sweeping"
    assert found <= recorded, sorted(found - recorded)
    # And the thing it must not find.
    digest = Registration.schema_fingerprint()[len(SCHEMA_PREFIX):]
    assert digest not in found
    # The document states the sweep it is swept with, verbatim.
    assert HASH_SWEEP in HISTORY_MD.read_text()


def test_the_untyped_fingerprint_still_names_the_same_shape(tmp_path):
    """A file stamped before the prefix landed is old, not unverifiable.

    Reporting `unverifiable_schema_change` over a file whose field names
    demonstrably match today's would be *cannot verify* said of something that
    can be verified, which is as false as the reverse.
    """

    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir()
    _complete_registration().save(p)
    raw = json.loads(p.read_text())
    assert raw["registered_schema"].startswith(SCHEMA_PREFIX)
    raw["registered_schema"] = raw["registered_schema"][len(SCHEMA_PREFIX):]
    p.write_text(json.dumps(raw))
    assert Registration.load(p).hash_verification == Registration.VERIFIED
    assert Registration.schema_matches(raw["registered_schema"])
    # A bare digest that is not this shape's digest is still not this shape.
    assert not Registration.schema_matches("0" * 16)
    assert not Registration.schema_matches(None)


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


CORRECTIONS = REPO_ROOT / "docs" / "CORRECTIONS.md"


def test_every_recurring_correction_class_has_an_invariant():
    """P122: what turns the corrections register from a list into an instrument.

    A register that only lists instances is a list. The rule this file imposes
    on itself is that a class with THREE OR MORE instances must carry an
    invariant, and this test is what holds it: adding a fourth instance to a
    class with no invariant fails here, at the moment the class is written down,
    rather than at the moment somebody notices the pattern two batches later.

    It is deliberately a test over the DOCUMENT. The classes are a judgement
    about what went wrong, and a judgement cannot be computed; what can be
    computed is that a judgement recording a recurrence has also recorded what
    would stop the next one.
    """

    text = CORRECTIONS.read_text()
    header = "| Class | Instances | Count | Invariant |"
    assert header in text, "the classes table is the instrument; it must exist"

    body = text.split(header, 1)[1].split("\n\n", 1)[0]
    rows = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in body.splitlines()
        if line.startswith("|") and not set(line.strip().strip("|")) <= set("-| ")
    ]
    assert rows, "the classes table has no rows"

    checked = 0
    for name, instances, count, invariant in rows:
        digits = re.sub(r"[^0-9]", "", count)
        if not digits:
            # A row with no count is not a class: it is the catch-all for rows
            # that belong to none. It owes no invariant and asserts no
            # recurrence, and treating it as a class would demand one.
            continue
        n = int(digits)
        # The count must match the instance list, or the table is asserting a
        # recurrence it has not enumerated.
        listed = len([i for i in instances.split(",") if i.strip()])
        assert n == listed or "itself" in instances or "and" in instances, (
            f"{name}: count {n} against {listed} listed instances"
        )
        if n < 3:
            continue
        checked += 1
        bare = invariant.replace("*", "").strip().lower()
        assert bare and bare not in {"n/a", "none", "tbd", "pending"}, (
            f"{name} has {n} instances and no invariant. A class that has "
            "recurred three times and carries no invariant is a class that "
            "will recur a fourth time."
        )
        assert "installed" in bare, (
            f"{name}: the invariant cell must say INSTALLED and where, so a "
            "reader can go and read the thing rather than take the word for it"
        )
    assert checked >= 1, "no recurring class found; the table cannot be right"



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
    # # | Quantity | Status | Scope | What unblocks it
    assert len(cells) == 5, cells[:2]
    return cells[2], cells[4]


def test_the_register_names_no_hash_outside_a_reference_to_the_history():
    """A hash in prose records a moment and is read as a state.

    `docs/OPEN_ITEMS.md` has named a superseded hash as the live one twice: the
    26 August stamp, overtaken by three re-stamps, and then its replacement,
    overtaken by one more. Both times the repair was written as though getting
    the number right were the fix, and both times it was overtaken again. This
    is the third repair and it is the one that does not need a fourth.

    **The exception is narrow and is exercised.** A hash naming what a reading
    was TAKEN UNDER is fixed for ever and may be written beside the history row
    that holds it; a hash naming what is CURRENT may not. The sweep is
    `HASH_SWEEP`, the same negative-lookaround pattern the schema fingerprint
    is swept with, so one pattern governs both records.
    """

    exercised = 0
    for n, line in enumerate(OPEN_ITEMS.read_text().splitlines(), 1):
        # Per line first, then per sentence, so a file mention on one line
        # cannot license a hash on the next.
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if not re.search(HASH_SWEEP, sentence):
                continue
            assert "REGISTRATION_HISTORY.md" in sentence, (
                f"{OPEN_ITEMS.name}:{n} names a hash outside a reference to "
                f"the history: {sentence.strip()[:160]}"
            )
            exercised += 1
    # A permitted branch nothing reaches is an untested allowance, which is the
    # defect class this suite exists against. Rows 21a and 21b use it.
    assert exercised >= 1, "the exception is never taken, so it is untested"


def test_the_register_states_the_rule_it_is_swept_under():
    """The prose cannot drift from the sweep that is run against it."""

    preamble = OPEN_ITEMS.read_text().split("## The binding path")[0]
    assert "No registration hash is written in this file" in preamble
    assert "test_the_register_names_no_hash_outside_a_reference_to_the_history" in preamble


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
    queue = text.split("## 5. The queue")[1].split("## 6.")[0]
    assert "Nothing outstanding: 1 draft(s). **These need a decision now.**" in queue
    assert queue.index("dir-zzz") < queue.index("dir-aaa") < queue.index("dir-mmm")
    ledger.close()


def _render(ledger, **over) -> str:
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    kwargs = dict(
        registration=reg, ledger=ledger, corpora=[("./corpora/us", "abcd")],
        commit="deadbeef", on=date(2026, 8, 27),
        # The real register, so the binding path is read against the document
        # that governs it.  No runs directory by default: a test that diffed
        # against whatever `docs/runs/` happens to hold would pass or fail on
        # the tree's history rather than on this code.
        register=OPEN_ITEMS,
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
    queue = _render(ledger).split("## 5. The queue")[1].split("## 6.")[0]

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
    # `origin` joined the header at P119; it is a provenance marker and not a
    # ranking key, and the check below is what holds that distinction rather
    # than the header literal alone.
    header = [l for l in queue.splitlines() if l.startswith("| outstanding |")]
    assert header == ["| outstanding | directive | class | origin | awaiting |"]
    for row in queue.splitlines():
        if not row.startswith("| ") or row.startswith("| outstanding |"):
            continue
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != 5 or set(cells[0]) <= set("-"):
            continue
        # Every cell after the first must be non-numeric: a second number
        # beside the count is a second ordering the reader can impose.
        for cell in cells[1:]:
            assert not cell.replace(".", "", 1).isdigit(), cell
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


def test_the_report_has_its_nine_sections_in_order():
    ledger = _report_ledger()
    text = _render(ledger)
    wanted = [
        "## 1. Binding path",
        "## 2. Provenance",
        "## 3. Intake funnel",
        "## 4. Fence report",
        "## 5. The queue",
        "## 6. Control arm",
        "## 7. Reason-code coverage",
        "## 8. Refutations",
        "## 9. Not measured",
    ]
    positions = [text.index(w) for w in wanted]
    assert positions == sorted(positions)
    ledger.close()


def test_the_provenance_header_carries_the_fingerprint_and_its_verdict():
    ledger = _report_ledger()
    prov = _render(ledger).split("## 2. Provenance")[1].split("## 3.")[0]
    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.hash() in prov
    assert reg.registered_schema in prov
    assert reg.hash_verification in prov
    assert "deadbeef" in prov and "abcd" in prov
    ledger.close()


def test_the_two_fence_arms_are_reported_apart_and_neither_is_rounded_up():
    ledger = _report_ledger()
    fences = _render(ledger).split("## 4. Fence report")[1].split("## 5.")[0]
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
    arm = _render(ledger).split("## 6. Control arm")[1].split("## 7.")[0]
    assert "**NOT YET RUN**" in arm
    assert "undetermined_at_budget" in arm and "claiming" in arm
    assert "not measured" in arm
    ledger.close()


def test_row_23_splits_the_control_arm_from_the_agent_arm(tmp_path):
    """P105: the third instance of one error, and the first found in code.

    P77 and P79 found §13 row 21 pooling a drawn arm with an authored one; P95
    found row 23 doing the same.  Both were readings published in a document.
    This one was in `_abort_positions`, which selected every intake refusal with
    no filter on `origin` and so added the random-mechanism control arm into the
    distribution of the agent arm it exists to be compared against.

    The fixture is built so that the two arms fail at DIFFERENT positions, which
    is what the live ledger does and what pooling hides: a pooled table would
    show both positions and attribute neither.
    """

    ledger = Ledger(parameter_hash="arm-split-test")
    for i in range(3):
        sid = f"prop-agent-{i}"
        ledger.write_proposal(sid, clean_proposal(), "abandoned_at_ingestion")
        ledger.write_refusal(
            summaries.render("proposal_names_entity", sid, {"entity": "Acme plc"})
        )
    for i in range(2):
        sid = f"prop-control-{i}"
        ledger.write_proposal(
            sid, clean_proposal(origin=Origin.RANDOM_CONTROL),
            "abandoned_at_ingestion",
        )
        ledger.write_refusal(
            summaries.render(
                "duplicate_of_open_pointer", sid,
                {"duplicate_ref": "dir-open", "population_key": "k"},
            )
        )

    dist = _render(ledger).split("### Abort-position distribution")[1]
    dist = dist.split("### Intake points")[0]

    # One column per arm, and each arm's failures under its own heading.
    assert "| pos | point | agent | random_control |" in dist
    assert "| 3 | `proposal_names_entity` | 3 | 0 |" in dist
    assert "| 7 | `duplicate_of_open_pointer` | 0 | 2 |" in dist

    # Kill rates per arm, never one rate over the two.
    assert "**agent**: intake kill rate 3/3 = **100.0%**" in dist
    assert "**random_control**: intake kill rate 2/2 = **100.0%**" in dist

    # The pooled figure survives as a comparison aid and says it is not a
    # reading, because a reader holding a pre-P105 report needs to see what
    # moved.
    assert "The pooled figure, retained and NOT a reading." in dist
    assert "total 5" in dist


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


CANDIDATES = REPO_ROOT / "docs" / "CANDIDATE_MECHANISMS.md"


def test_the_candidate_list_carries_no_ranking_key_but_the_criteria_count():
    """P129: the deliverable may not rank, and plausibility is the one to name.

    The list is ordered by number of achievability criteria met, which is a
    count of registered constraints satisfied and therefore arithmetic over the
    parameter object. Any other key would be this file telling the operator
    which mechanism to believe, which is the clerk becoming an analyst.

    The check is over the STRUCTURE with no exemption, and over the prose less
    the sentences that exist to disclaim the words. Rewording a disclaimer fails
    this test and sends the next reader back to it.
    """

    text = CANDIDATES.read_text()

    structure = "\n".join(
        l for l in text.splitlines() if l.startswith(("|", "#"))
    ).lower()
    for word in RANKING_WORDS + ("plausib", "confidence", "likelihood"):
        assert word not in structure, word

    disclaimers = (
        "**By number of achievability criteria MET, descending. Then\n"
        "alphabetically by mechanism.**\n",
        "No merit, no severity, no score, no plausibility, no\nrecency, no "
        "confidence.",
        "***Plausibility is named explicitly because it is the one a model "
        "would reach\nfor.*** A model-derived plausibility ranking is the "
        "clerk becoming an analyst,",
        "**The alphabetical tie-break ranks nothing**",
    )
    prose = text
    for d in disclaimers:
        assert d in text, d
        prose = prose.replace(d, "")
    # `score` is deliberately NOT checked in the prose: the lens's own third
    # state is `unscorable`, and a file that may not name the vocabulary of the
    # thing it reports cannot describe it. It IS checked in the structure
    # above, which is where a ranking key would live.
    for word in ("merit", "severity", "plausib", "confidence", "recency"):
        assert word not in prose.lower(), word

    # And it must say what it is not, in terms a reader cannot skim past.
    for claim in (
        "It is NOT evidence that any of them works",
        "Zero backtests. Zero frozen designs. Zero trades.",
        "A reader must not be able to mistake this list for results",
    ):
        assert claim in text, claim


def test_the_achievability_lens_reports_and_refuses_nothing():
    """P128: a LENS, not a fence, and the third state is not a pass.

    Every criterion is derived from a registered decision, so the lens reads the
    parameter object rather than holding numbers of its own. It reports; it
    refuses nothing and no funnel step consults it, which is what keeps it
    procedure under armed §0.6. The fence version is apparatus and is prepared
    in Annex A.1, not taken.

    The state that matters is UNSCORABLE. A criterion the register cannot judge
    is not met and is not failed, and counting it as met would be the defect §2
    names: a check that could not run recorded as one that ran.
    """

    from fntn.scanner import achievability as ach

    strong = ach.Candidate(
        "m-strong", origin="agent", long_only=True, us_listed=True,
        min_share_price_usd=25.0, median_daily_notional_usd=5_000_000,
        survives_to_next_open=True, claimed_effect_bps=40.0,
        holding_period_sessions=21, obtainable_without_purchase=True,
    )
    r = ach.score(strong, tolerance_bps=10.0, delta_min_floor_bps=17.0,
                  smallest_position_usd=2418.75)
    assert r.met == 8
    assert r.failed == []
    # The archive does not exist, so this one cannot be scored either way.
    assert r.unscorable == ["backtestable"]

    # Every criterion cites the decision behind it. A criterion whose authority
    # is not written down is a preference wearing a derivation's clothes.
    assert all(c.authority.strip() for c in r.criteria)

    weak = ach.Candidate(
        "m-weak", origin="random_control", long_only=False, us_listed=False,
        min_share_price_usd=3.0, median_daily_notional_usd=10_000,
        survives_to_next_open=False, claimed_effect_bps=4.0,
        holding_period_sessions=7, obtainable_without_purchase=False,
    )
    w = ach.score(weak, tolerance_bps=10.0, delta_min_floor_bps=17.0,
                  smallest_position_usd=2418.75)
    assert w.met == 0
    assert len(w.failed) == 8
    # The failing criterion is NAMED, never merely counted.
    assert "min_share_price" in w.failed and "effect_exceeds_delta_min" in w.failed

    # An absent declaration is unscorable, never a failure: the two are
    # different claims about the candidate and are reported apart.
    silent = ach.Candidate("m-silent", origin="agent")
    q = ach.score(silent, tolerance_bps=10.0, delta_min_floor_bps=17.0,
                  smallest_position_usd=2418.75)
    assert q.met == 0 and q.failed == [] and len(q.unscorable) == 9

    # And the two derived thresholds are derived, not held.
    assert round(ach.minimum_share_price_usd(10.0), 2) == 10.42
    assert round(ach.minimum_daily_notional_usd(2418.75)) == 40312
    # An unset tolerance yields no floor rather than a default one.
    assert ach.minimum_share_price_usd(None) is None


def test_the_unexercised_list_splits_by_arm_like_the_distribution(tmp_path):
    """P126: the fourth instance of a class whose invariant was installed at P105.

    P105 split the abort-position distribution by `origin`, because pooling the
    agent arm with the random-mechanism control arm destroys the comparison the
    control arm exists for. The method BESIDE it kept the pooled query and went
    on projecting `origin` away, so a point exercised only by the control arm
    was reported as exercised when for the agent arm it was not.

    The invariant was applied to a method when the class was about a query.
    Found by sweeping every SELECT in the package for markers the fences rely
    on, which is what the class's invariant should have said to do.
    """

    ledger = Ledger(parameter_hash="unexercised-arms")
    # The agent arm trips position 3 only; the control arm trips position 7
    # only. Pooled, both look exercised. Split, each arm is missing the other's.
    for did, origin, code in (
        ("prop-a", Origin.AGENT, "proposal_names_entity"),
        ("prop-c", Origin.RANDOM_CONTROL, "duplicate_of_open_pointer"),
    ):
        ledger.write_proposal(did, clean_proposal(origin=origin),
                              "abandoned_at_ingestion")
        ledger.write_refusal(summaries.render(code, did, {
            "entity": "Acme plc", "duplicate_ref": "dir-open",
            "population_key": "k",
        }))

    section = _render(ledger).split("### Intake points not exercised")[1]
    section = section.split("## 4.")[0]
    agent = section.split("**agent:")[1].split("**random_control:")[0]
    control = section.split("**random_control:")[1]

    # The control arm's point is unexercised FOR THE AGENT, and vice versa.
    assert "`duplicate_of_open_pointer`" in agent
    assert "`proposal_names_entity`" not in agent
    assert "`proposal_names_entity`" in control
    assert "`duplicate_of_open_pointer`" not in control

    # Eleven of twelve for each arm, and the pooled ten printed as not a
    # reading so a reader holding an earlier report can see what moved.
    assert "**agent: 11 of 12 unexercised**" in section
    assert "**random_control: 11 of 12 unexercised**" in section
    assert "Pooled, and NOT a reading: 10 of 12." in section
    ledger.close()


def test_unexercised_intake_points_are_named_not_counted():
    ledger = _report_ledger()
    section = _render(ledger).split("### Intake points not exercised")[1].split("## 4.")[0]
    for code in codes.INTAKE_ORDER:
        assert f"`{code}`" in section
    ledger.close()


def test_the_refutations_section_is_seeded_with_the_three_to_date():
    ledger = _report_ledger()
    ref = _render(ledger).split("## 8. Refutations")[1].split("## 9.")[0]
    assert "94%" in ref
    assert "Trust Holdings and Transactions" in ref
    assert "RAW FETCHED PAGES WERE NEVER RETAINED" in ref
    assert len(report_mod.STANDING_REFUTATIONS) == 3
    ledger.close()


# ---------------------------------------------------------------------------
# Section 1: the binding path, and what moved.
# ---------------------------------------------------------------------------


def _flip(row: str):
    """A status for ``row`` that DIFFERS from the one the register holds today.

    Returns ``(cell, from_token, to_token)``.

    **Why this exists (P117).** Two fixtures below edited §13 row 1 to
    ``**CLOSED**`` to simulate binding-path movement. Row 1 closed on 27 August
    2026, so the edit became a **no-op** and the fixtures went on passing whilst
    testing nothing, until the movement assertions failed for the right reason
    and exposed it. A fixture that silently stops changing anything is the
    failure class this suite exists against, so the flip is computed from the
    register rather than written as a literal.
    """

    live = report_mod.status_token(_open_items_row(row)[0])
    if live == "CLOSED":
        return "**BLOCKED**", "CLOSED", "NOT CLOSED"
    return "**CLOSED**", "NOT CLOSED", "CLOSED"


def _register_copy(tmp_path, edits) -> Path:
    """`docs/OPEN_ITEMS.md` with named §13 rows' status cells replaced."""

    lines = OPEN_ITEMS.read_text().splitlines()
    for row, status in edits.items():
        hit = 0
        for i, line in enumerate(lines):
            if line.startswith(f"| {row} |"):
                cells = line.strip().strip("|").split("|")
                # Refuse a no-op. An edit that changes nothing makes every
                # assertion downstream vacuous, and it does so silently.
                assert cells[2].strip() != status.strip(), (
                    f"row {row} already reads {status}, so this edit changes "
                    "nothing and the fixture would assert nothing"
                )
                cells[2] = f" {status} "
                lines[i] = "|" + "|".join(cells) + "|"
                hit += 1
        assert hit == 1, f"expected one row {row}, edited {hit}"

    out = tmp_path / "OPEN_ITEMS.md"
    out.write_text("\n".join(lines) + "\n")
    return out


def test_the_binding_path_is_first_and_sits_above_the_provenance_header():
    """The order is the point, not merely the presence.

    The provenance header answers *under what was this run taken*; the binding
    path answers *has the project moved*. A reader opening the file for the
    second question should not have to find it under the first.
    """

    ledger = _report_ledger()
    text = _render(ledger)
    assert text.index("## 1. Binding path") < text.index("## 2. Provenance")
    # And above it in the file, not merely numbered before it.
    assert text.index("## 1. Binding path") < text.index("registration hash")
    ledger.close()


def test_every_binding_path_status_is_read_from_the_register(tmp_path):
    """Read, not stated. Move the register and the section moves with it."""

    before = report_mod.binding_path_rows(OPEN_ITEMS)
    assert [r[0] for r in before] == ["1", "2", "3", "4", "5"]
    # Read against the register's own cell rather than a literal, so this test
    # asserts the reading and not today's value of row 1.
    row1 = report_mod.status_token(_open_items_row("1")[0])
    assert before[0][3] == f"§13 row 1: {row1}"
    assert before[0][2] == ("CLOSED" if row1 == "CLOSED" else "NOT CLOSED")

    cell, _, to_token = _flip("1")
    after = report_mod.binding_path_rows(_register_copy(tmp_path, {"1": cell}))
    assert after[0][2] == to_token
    assert after[0][3] == f"§13 row 1: {cell.strip('*')}"
    # Row 1 is also one of the twenty-seven step 5 waits on, so step 5's
    # evidence moves too whilst its status does not.
    assert after[4][2] == "NOT CLOSED"
    assert after[4][3] != before[4][3]


def test_a_part_closure_does_not_close_a_step_and_prints_its_scope():
    """`PART CLOSED` is a closure over the scope in the Scope column.

    Reading one as done would say the binding path had moved when the register
    says it has not, which is the one thing this section must not do.
    """

    assert report_mod.is_closed("CLOSED")
    for token in ("PART CLOSED", "PROVISIONAL", "BLOCKED", "OPEN"):
        assert not report_mod.is_closed(token)
    # Rows 22 and 25 are both PART CLOSED over the US, and step 2 names both.
    step2 = report_mod.binding_path_rows(OPEN_ITEMS)[1]
    assert step2[2] == "NOT CLOSED"
    assert step2[3] == "§13 row 22: PART CLOSED (US); §13 row 25: PART CLOSED (US)"


def test_the_register_carries_only_its_five_declared_statuses():
    """Declared once, in the register's preamble, and used nowhere loosely."""

    rows = report_mod.register_rows(OPEN_ITEMS.read_text())
    assert set(rows) == {"13", "14d", "14p"}
    seen = {
        report_mod.status_token(row["Status"])
        for table in rows.values() for row in table.values()
    }
    assert seen <= set(report_mod.REGISTER_STATUSES), seen - set(
        report_mod.REGISTER_STATUSES)
    # And the preamble declares exactly those five, so the vocabulary is in
    # one place rather than two.
    preamble = OPEN_ITEMS.read_text().split("## The binding path")[0]
    for status in report_mod.REGISTER_STATUSES:
        assert f"`{status}`" in preamble
    assert "Scope is a column and never a status" in preamble


def test_a_status_outside_the_five_is_refused_and_never_repaired(tmp_path):
    """An earlier reader took everything up to the first colon and so silently
    repaired a cell carrying a note where a status belongs. A vocabulary kept
    in two places is widened in the second one."""

    doc = _register_copy(tmp_path, {"1": "**CLOSED for US**"})
    step1 = report_mod.binding_path_rows(doc)[0]
    assert step1[2] == "CANNOT READ THE REGISTER"
    assert "outside the register's declared status vocabulary" in step1[3]
    assert "CLOSED for US" in step1[3]

    # A note where a status belongs is refused for the same reason.
    doc = _register_copy(tmp_path, {"1": "**OPEN**: waiting on the schedule"})
    assert report_mod.binding_path_rows(doc)[0][2] == "CANNOT READ THE REGISTER"

    # And an unreadable file is still its own, different refusal.
    gone = report_mod.binding_path_rows(tmp_path / "no-such-register.md")
    assert all(r[2] == "CANNOT READ THE REGISTER" for r in gone)
    assert "no-such-register.md" in gone[0][3]


def test_a_register_that_cannot_be_read_refuses_rather_than_defaulting(tmp_path):
    """A step reported outstanding when nothing was read is a refusal in
    a reading's clothes, and rule 3 forbids it."""

    rows = report_mod.binding_path_rows(tmp_path / "there-is-no-register.md")
    assert len(rows) == 5
    assert all(r[2] == "CANNOT READ THE REGISTER" for r in rows)
    assert all("NOT CLOSED" != r[2] for r in rows)

    ledger = _report_ledger()
    text = _render(ledger, register=None)
    assert "**No register was given, so no status was read.**" in text
    assert "no binding-path movement since" not in text
    ledger.close()


def test_the_movement_line_says_the_exact_words_when_nothing_moved(tmp_path):
    """`no binding-path movement since <previous report>`, and nothing softer."""

    ledger = _report_ledger()
    runs = tmp_path / "runs"
    runs.mkdir()
    first = _render(ledger, runs_dir=runs)
    (runs / "2026-08-27_funnel.md").write_text(first)
    second = _render(ledger, runs_dir=runs)
    assert "**no binding-path movement since 2026-08-27_funnel.md**" in second
    ledger.close()


def test_the_movement_line_names_the_step_that_moved(tmp_path):
    """Computed by diffing the previous file, never asserted."""

    ledger = _report_ledger()
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "2026-08-27_funnel.md").write_text(_render(ledger, runs_dir=runs))
    cell, from_token, to_token = _flip("1")
    moved = _render(
        ledger, runs_dir=runs,
        register=_register_copy(tmp_path, {"1": cell}),
    )
    assert "no binding-path movement" not in moved
    assert "**Moved since 2026-08-27_funnel.md:**" in moved
    assert f"- step 1: **{from_token}** to **{to_token}**" in moved
    # Step 5's status held and its evidence moved, and both are said.
    assert "- step 5: **NOT CLOSED** to **NOT CLOSED**; register cells were" in moved
    ledger.close()


def test_a_previous_report_without_a_binding_path_is_not_called_no_movement(tmp_path):
    """A comparison that did not happen cannot have come out equal.

    Every report in `docs/runs/` written before this section exists is this
    case, so the wrong answer here would be the first thing a reader saw.
    """

    ledger = _report_ledger()
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "2026-08-27_funnel.md").write_text("# Run report\n\n## 1. Provenance\n")
    text = _render(ledger, runs_dir=runs)
    assert "no binding-path movement since" not in text
    assert "carries no binding path, so nothing was diffed" in text
    assert "**This is not the same as no movement**" in text
    ledger.close()


def test_no_previous_report_at_all_is_not_called_no_movement(tmp_path):
    ledger = _report_ledger()
    runs = tmp_path / "runs"
    runs.mkdir()
    text = _render(ledger, runs_dir=runs)
    assert "no binding-path movement since" not in text
    assert "so nothing was diffed" in text
    ledger.close()


def test_the_previous_report_is_the_latest_one_next_path_would_follow(tmp_path):
    """The ordering `next_path` allocates, read back."""

    for name in ("2026-08-26_funnel.md", "2026-08-27_funnel.md",
                 "2026-08-27_funnel_02.md", "2026-08-27_funnel_10.md"):
        (tmp_path / name).write_text("x")
    assert report_mod.previous_report(tmp_path).name == "2026-08-27_funnel_10.md"
    assert report_mod.previous_report(tmp_path / "nothing-here") is None


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


# ---------------------------------------------------------------------------
# The trace-filings corpus fence (§9.4, phase 2a).
#
# `corpora/_trace_filings/` holds SEC Form 4 filings for the trace harness.
# It names issuers and dates, which is exactly the material the entity fence
# exists to keep OUT of a proposal.  **It must not be reachable by the
# discovery agent under any code path**, and the containment is asserted here
# before anything is fetched into it.
#
# These tests were written to FAIL first, against a deliberately mis-registered
# route, and the refusals were added afterwards.  A fence written after the
# code it fences is a fence shaped to let the code through.
# ---------------------------------------------------------------------------

from fntn.scanner.markets import CorpusInvalid

TRACE_FILINGS = "corpora/_trace_filings"


@pytest.mark.parametrize("route", [
    TRACE_FILINGS,
    "./corpora/_trace_filings",
    "corpora/_trace_filings/",
    "corpora/_trace_filings/2026",          # a subdirectory of it
    "corpora/us/_raw",                       # the existing underscore store
    "/abs/path/corpora/_trace_filings",
    "corpora/_anything_at_all",
])
def test_no_registration_route_can_resolve_to_an_underscore_directory(route):
    """The deliberately mis-registered route, refused at construction.

    Refused in `Corpus.__post_init__` rather than in `missing()`, because
    `missing()` returns advice and advice is not a fence: a registration
    naming this route must be **unconstructible**, so a file naming it will
    not load at all.
    """

    with pytest.raises(CorpusInvalid, match="underscore"):
        RegCorpus(
            corpus_id="mis-registered",
            market="us",
            partition="discovery",
            retrieval_route=route,
            scoring_mode="pre_archive",
        )


def test_a_registration_file_naming_the_trace_corpus_will_not_load(tmp_path):
    """Not merely refused when built by hand: refused when read off disk."""

    p = tmp_path / REGISTRATION_FILE
    (tmp_path / "docs").mkdir()
    _complete_registration().save(p)
    raw = json.loads(p.read_text())
    raw["corpora"].append({
        "corpus_id": "trace-filings",
        "market": "us",
        "partition": "discovery",
        "retrieval_route": TRACE_FILINGS,
        "scoring_mode": "pre_archive",
    })
    p.write_text(json.dumps(raw))
    with pytest.raises(CorpusInvalid, match="underscore"):
        Registration.load(p)


def test_the_corpus_loader_skips_underscore_directories_at_the_top_level(tmp_path):
    """Within one was already skipped. The top level was not.

    `cmd_sweep` skipped underscore-prefixed *files inside* a route and read
    everything else, so a route pointed AT an underscore directory had its
    contents read in full. The skip now applies to the route itself.
    """

    from fntn.scanner.corpusio import corpus_documents

    ordinary = tmp_path / "us"
    ordinary.mkdir()
    (ordinary / "doc.txt").write_text("a filing-free rule text")
    (ordinary / "_manifest.tsv").write_text("bookkeeping\tnot corpus")
    assert corpus_documents(ordinary) == ["a filing-free rule text"]

    fenced = tmp_path / "_trace_filings"
    fenced.mkdir()
    (fenced / "form4.txt").write_text("ACME CORP  2026-08-27  purchase")
    assert corpus_documents(fenced) == []

    nested = tmp_path / "_trace_filings" / "2026"
    nested.mkdir()
    (nested / "form4.txt").write_text("ACME CORP  2026-08-27  purchase")
    assert corpus_documents(nested) == []


def test_discovery_reaches_no_module_that_names_the_trace_corpus():
    """An import fence over a path, not over a package.

    The existing fence forbids modules carrying prices and outcomes. This one
    forbids the *string*: no module in `discovery.py`'s transitive import
    closure may name the trace corpus, because naming it is the first step of
    reading it.
    """

    from fntn.scanner.fences import discovery_import_closure

    src = REPO_ROOT / "src"
    named = []
    for name in sorted(discovery_import_closure()):
        if not name.startswith("fntn."):
            continue
        path = src / (name.replace(".", "/") + ".py")
        if path.exists() and "_trace_filings" in path.read_text():
            named.append(name)
    assert named == [], named


def test_the_fetcher_is_outside_the_discovery_import_closure():
    """The instrument that writes the corpus is not reachable from the agent."""

    from fntn.scanner.fences import discovery_import_closure

    closure = discovery_import_closure()
    assert "fntn.scanner.trace_filings" not in closure
    # And it does name the corpus, so the test above is testing something.
    src = REPO_ROOT / "src" / "fntn" / "scanner" / "trace_filings.py"
    assert "_trace_filings" in src.read_text()


# ---------------------------------------------------------------------------
# The trace-filings fetcher (§9.4, phase 2b).
# ---------------------------------------------------------------------------

from fntn.scanner import trace_filings as tf
from fntn.scanner.trace_filings import ResponseNotTheDocument, TraceCorpusRefused

INDEX_FIXTURE = """Description:           Daily Index of EDGAR Dissemination Feed
Last Data Received:    August 27, 2026

Form Type   Company Name                                       CIK         Date Filed  File Name
---------------------------------------------------------------------------------------------------
3           EXAMPLE HOLDINGS INC                               0000111111  2026-08-27  edgar/data/111111/a.txt
4           ACME CORP                                          0000320193  2026-08-27  edgar/data/320193/b.txt
4           NORTHERN TRUST HOLDINGS PLC                        0000222222  2026-08-27  edgar/data/222222/c.txt
4/A         AMENDED FILER LTD                                  0000333333  2026-08-27  edgar/data/333333/d.txt
8-K         SOMETHING ELSE CO                                  0000444444  2026-08-27  edgar/data/444444/e.txt
8-K         BOREALIS MINING PLC                                0000555555  2026-08-27  edgar/data/555555/f.txt
8-K/A       AMENDED EIGHT K CO                                 0000666666  2026-08-27  edgar/data/666666/g.txt
"""


def test_the_fetch_refuses_when_SEC_CONTACT_is_unset(monkeypatch):
    """Refused, not defaulted, and deliberately not substitutable.

    A placeholder User-Agent is a false statement made to a regulator's server
    in order to obtain data, and it would be recorded on every manifest row as
    though it were the contact.
    """

    monkeypatch.delenv("SEC_CONTACT", raising=False)
    with pytest.raises(TraceCorpusRefused, match="THE OPERATOR MUST SET IT"):
        tf.user_agent()
    monkeypatch.setenv("SEC_CONTACT", "   ")
    with pytest.raises(TraceCorpusRefused, match="SEC_CONTACT is not set"):
        tf.user_agent()
    # And the block refuses before it writes anything, not part-way through.
    monkeypatch.delenv("SEC_CONTACT", raising=False)
    with pytest.raises(TraceCorpusRefused):
        tf.fetch_block(date(2026, 8, 27))


def test_the_user_agent_carries_the_operator_contact(monkeypatch):
    """The address is no longer an `example.com` one, and that is the point.

    This test asserted that `a.person@example.com` was accepted until 27 August
    2026. RFC 2606 reserves that domain for documentation and no mail reaches
    it, so it is exactly the unedited-template case the guard now refuses, and
    a test asserting it was accepted was asserting the defect.
    """

    monkeypatch.setenv("SEC_CONTACT", "A Person a.person@a-real-domain.uk")
    assert "A Person a.person@a-real-domain.uk" in tf.user_agent()


def test_a_SET_SEC_CONTACT_can_still_be_unusable(monkeypatch):
    """P136. The guard tested presence and its own docstring is about content.

    Found by running the reconciliation rather than by reading the code: this
    session's environment had `SEC_CONTACT` set to the literal string
    `<name> <email>`, which `if not contact` admitted. It would have been sent
    to sec.gov in a User-Agent on every request of a hundred-filing fetch.
    """

    # The exact string this session found in its own environment.
    monkeypatch.setenv("SEC_CONTACT", "<name> <email>")
    with pytest.raises(TraceCorpusRefused, match="unedited placeholder"):
        tf.user_agent()

    # A documentation domain is a placeholder even where nothing is bracketed.
    monkeypatch.setenv("SEC_CONTACT", "Your Name your.address@example.com")
    with pytest.raises(TraceCorpusRefused, match="unedited placeholder"):
        tf.user_agent()

    # A name with no address identifies nobody the SEC could write to.
    monkeypatch.setenv("SEC_CONTACT", "Ada Lovelace")
    with pytest.raises(TraceCorpusRefused, match="no email address"):
        tf.user_agent()
    monkeypatch.setenv("SEC_CONTACT", "Ada Lovelace ada@localhost")
    with pytest.raises(TraceCorpusRefused, match="no email address"):
        tf.user_agent()

    # And the refusal happens before anything is fetched or written.
    monkeypatch.setenv("SEC_CONTACT", "<name> <email>")
    with pytest.raises(TraceCorpusRefused, match="unedited placeholder"):
        tf.fetch_block(date(2026, 8, 27))


def test_a_SET_ANTHROPIC_API_KEY_can_still_be_unusable(monkeypatch):
    """P136, the same defect in the other credential guard, on the same day.

    `AnthropicClient` tested `if not key` and promised in its own docstring
    that "a misconfiguration surfaces before a sweep is half-run". A key set to
    a ten-character stub satisfied the test, and the sweep failed at the API
    after the registration, the master and the corpora had all been loaded.

    The preflight is a real call to `models.retrieve`, which costs no tokens
    and settles the key and the model identifier together. A shape or length
    test was considered and rejected: it encodes a guess about how keys are
    formatted, and the question is not what the key looks like.
    """

    import anthropic
    import httpx2

    from fntn.scanner.clients import AnthropicClient, ClientRefusal

    def _raiser(exc):
        class _Models:
            def list(self, **_kw):
                raise exc

        class _Fake:
            def __init__(self, *a, **kw):
                self.models = _Models()

        return _Fake

    request = httpx2.Request("GET", "https://api.anthropic.com/v1/models/x")
    response = httpx2.Response(401, request=request)

    # An unusable key is refused at CONSTRUCTION, naming the true cause.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-stub")
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        _raiser(anthropic.AuthenticationError("API key is invalid.",
                                              response=response, body=None)),
    )
    with pytest.raises(ClientRefusal, match="SET IS NOT USABLE"):
        AnthropicClient(model="claude-anything")

    # A model the key cannot reach is refused too, and NOT substituted: which
    # model read the corpus is part of what a proposal is replayable against.
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        _raiser(anthropic.NotFoundError("no such model",
                                        response=httpx2.Response(404, request=request),
                                        body=None)),
    )
    with pytest.raises(ClientRefusal, match="not available to this key"):
        AnthropicClient(model="claude-anything")

    # A network failure is reported as one and never as an empty sweep.
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        _raiser(anthropic.APIConnectionError(request=request)),
    )
    with pytest.raises(ClientRefusal, match="reported as a network failure"):
        AnthropicClient(model="claude-anything")

    # An absent key still refuses before any of that is reached.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ClientRefusal, match="no API key"):
        AnthropicClient(model="claude-anything")


def test_the_preflight_refuses_a_pinned_model_the_key_cannot_see(monkeypatch):
    """P137. Written against a FABRICATED id, and it fails without the check.

    The preflight enumerates rather than retrieving: `models.retrieve` answers
    *is this id resolvable*, `models.list` answers *what does this key actually
    have*, and only the second lets the refusal name the alternatives.

    The reason for widening it is not that any pin was found stale -- that
    claim was made from a cached table and was wrong (B14). It is that FOUR
    separate failures, an absent key, a stub key, a model question settled
    without the authoritative source, and a call the API would have rejected,
    were each found only by running the whole thing.
    """

    from types import SimpleNamespace

    import anthropic

    from fntn.scanner.clients import AnthropicClient, ClientRefusal

    class _Models:
        def __init__(self, ids):
            self._ids = ids

        def list(self, **_kw):
            return SimpleNamespace(data=[SimpleNamespace(id=i) for i in self._ids])

    def _fake(ids):
        class _Fake:
            def __init__(self, *a, **kw):
                self.models = _Models(ids)

        return _Fake

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-whatever-this-is-not-checked")

    # A fabricated id the key cannot see: REFUSED, and the refusal names what
    # is actually there rather than leaving the operator to guess.
    monkeypatch.setattr(anthropic, "Anthropic", _fake(["claude-real-1", "claude-real-2"]))
    with pytest.raises(ClientRefusal) as exc:
        AnthropicClient(model="claude-fabricated-9")
    assert "claude-fabricated-9" in str(exc.value)
    assert "claude-real-1" in str(exc.value), "the refusal must name the alternatives"
    assert "REFUSED rather than substituting" in str(exc.value)

    # A pin the key CAN see constructs, and records what the preflight
    # established without inferring anything it did not.
    monkeypatch.setattr(anthropic, "Anthropic", _fake(["claude-real-1", "claude-real-2"]))
    c = AnthropicClient(model="claude-real-2")
    assert c._preflight["model"] == "claude-real-2"
    assert c._preflight["models_visible"] == 2
    # THE CREDIT STATE IS REPORTED AS UNESTABLISHED. The models endpoint does
    # not consult the balance, and reading "the endpoint answered" as "there is
    # credit" is the partial-view conclusion this preflight exists because of.
    assert "not established" in c._preflight["credit"]


def test_the_client_no_longer_claims_temperature_zero():
    """P136. The API removed the parameter; the docstring had to follow it.

    `messages.create` in `anthropic` 1.x does not accept `temperature`, and the
    current models reject sampling parameters outright. The call carried
    `temperature=0` and raised TypeError before it ever reached authentication,
    so the sweep could not have run even with a working key.

    What is asserted here is the honesty of the record, not the absence of a
    keyword: a class that says "temperature zero" in its own name-line while
    the API refuses the parameter is a claim this project would have to
    withdraw later.
    """

    import inspect

    from fntn.scanner import clients

    source = inspect.getsource(clients.AnthropicClient.complete)
    assert "temperature" not in source.split('"""')[2], (
        "the call must not pass temperature: 1.x does not accept it"
    )
    doc = inspect.getdoc(clients.AnthropicClient) or ""
    assert "NO LONGER temperature zero" in doc
    # And the thing that was NOT lost is named, because that is what makes the
    # withdrawal a finding rather than a shrug.
    assert "TranscriptClient" in doc and "registered seed" in doc


def test_a_blank_market_cell_is_not_attributed_to_the_filename(tmp_path):
    """P137. Found by Class V's own sweep, one commit after the invariant.

    `load_csv` read the market column as
    `(row.get(mkt_col) or "").strip() or default_market`, and `default_market`
    is the FILE STEM where the operator names no market. So a row with a blank
    exchange cell was counted into a market that never claimed it, and
    `coverage = rows / listed_total` rose accordingly.

    The comment eight lines above that line already stated the rule it broke:
    an earlier version collapsed markets and reported a figure that "looks like
    a measurement", which is worse than none.

    Class V's second clause is what asks for the case below: material that is
    PRESENT and well-formed and wrong, not absent.
    """

    from fntn.scanner.master import SecurityMaster

    csv_path = tmp_path / "asx.csv"
    csv_path.write_text(
        "name,ticker,exchange\n"
        "Attributed Holdings,AAA,ASX\n"
        "Also Attributed Ltd,BBB,ASX\n"
        "Blank Cell Corp,CCC,\n",          # present, well-formed, unattributed
        encoding="utf-8",
    )

    m = SecurityMaster()
    m.load_csv(csv_path)                     # no market named: the live shape

    assert m.per_market["ASX"].rows == 2, (
        "only the rows that named ASX may be counted as ASX coverage"
    )
    assert "asx (unattributed)" in m.per_market
    assert m.per_market["asx (unattributed)"].rows == 1

    # The blank row is NOT counted into the file-stem market.
    assert "asx" not in m.per_market or m.per_market["asx"].rows == 0

    # An unattributed bucket has no population to be measured against, so it
    # reports coverage UNKNOWN rather than passing a floor it never met.
    unreadable = m.unreadable_markets(0.95)
    assert "asx (unattributed)" in unreadable
    assert "coverage unknown" in unreadable["asx (unattributed)"]

    # AND THE FENCE IS UNWEAKENED: the blank row's issuer still binds, because
    # names and tickers are global. Only the coverage ATTRIBUTION changed.
    assert "ccc" in m.tickers
    assert any("blank cell" in n for n in m.names)


def test_the_698_byte_stub_is_reported_and_never_worked_around():
    """The failure a previous session actually hit, asserted as itself.

    A 200 carrying a stub looks like success, which is why it cost real time.
    Filing it as a transport error would put it under the heading nobody
    re-reads.
    """

    stub = b"<html><body>Your request has been identified as automated.</body></html>"
    stub += b" " * (698 - len(stub))
    with pytest.raises(ResponseNotTheDocument, match="698 bytes"):
        tf.verify_response("http://x", stub, tf.MIN_HEADER_BYTES + 1000,
                           tf.HEADER_MARKER)
    # And on the prose path, which has no structural marker to fall back on:
    # the floor is the only size check there is, so it must still catch this.
    with pytest.raises(ResponseNotTheDocument, match="698 bytes"):
        tf.verify_prose_response("http://x", stub, tf.MIN_RELEASE_BYTES)


def test_a_plausible_size_without_the_marker_is_still_not_the_document():
    """The size catches one stub; the marker catches the class it belongs to."""

    body = ("<html>" + "x" * 4000 + "</html>").encode()
    with pytest.raises(ResponseNotTheDocument, match="ACCESSION-NUMBER"):
        tf.verify_response("http://x", body, tf.MIN_HEADER_BYTES,
                           tf.HEADER_MARKER)
    good = ("<ACCESSION-NUMBER>0001-26-1" + "x" * 4000).encode()
    assert tf.HEADER_MARKER in tf.verify_response(
        "http://x", good, tf.MIN_HEADER_BYTES, tf.HEADER_MARKER)


def test_the_prose_path_states_what_it_cannot_establish_and_still_catches_the_stub():
    """B17's honest half: a free-form release has NO structural marker.

    A Form 4 carries `<ownershipDocument`. An earnings release carries nothing
    every instance has and no error page could, so inventing a marker would be
    a check that passes on EDGAR's error page or fails on a valid release.
    **The compensating control is that the filename came from the regulator's
    own manifest for that accession**, and what remains is a floor plus the
    stub markers this project has actually observed.
    """

    release = ("<html><body>" + "Third quarter results. " * 200
               + "</body></html>").encode()
    assert "Third quarter" in tf.verify_prose_response(
        "http://x", release, tf.MIN_RELEASE_BYTES)

    # EDGAR's own throttle page is large enough to clear any floor.
    throttled = ("<html><head><title>SEC.gov | Request Rate Threshold "
                 "Exceeded</title></head><body>" + "x" * 4000
                 + "</body></html>").encode()
    with pytest.raises(ResponseNotTheDocument, match="error page"):
        tf.verify_prose_response("http://x", throttled, tf.MIN_RELEASE_BYTES)


def test_the_index_is_parsed_deterministically_and_amendments_are_excluded():
    """A field-delimited form gets a parser, not a clerk (CLAUDE.md rule 1).

    **Amendments are excluded and that is a choice, not an accident.** A `4/A`
    restates a filing already in the flow, so including it would count one
    event twice in any distribution taken over the corpus. It is stated here
    so the next reader finds the reason rather than the behaviour.
    """

    rows = tf.eight_k_rows(INDEX_FIXTURE)
    assert [r[0] for r in rows] == ["0000444444", "0000555555"]
    assert [r[1] for r in rows] == ["SOMETHING ELSE CO", "BOREALIS MINING PLC"]
    assert rows[0][2] == "edgar/data/444444/e.txt"
    # `8-K/A` is excluded: an amendment's ingestion lag is measured against the
    # amendment's own date and says nothing about how promptly the ORIGINAL
    # reached this system, which is what §13 row 15 is short of.
    assert not [r for r in rows if "AMENDED" in r[1]]
    # Form 4 is no longer taken at all: step 4 was RE-POINTED (§12.1 P126) and
    # the fetcher followed it a batch late (B17).
    assert not [r for r in rows if r[0] == "0000320193"]


def test_the_header_view_yields_item_numbers_and_the_document_manifest():
    """B17. The daily index has no items, so the header view is what filters.

    Item NUMBERS and not titles: the full submission writes
    `ITEM INFORMATION: Results of Operations and Financial Condition`, which is
    a wording that can drift, and `<ITEMS>2.02`, which cannot.
    """

    header = """<HTML><HEAD><TITLE>SEC EDGAR Submission</TITLE>
<!--
<ACCESSION-NUMBER>0001213900-26-093981
<TYPE>8-K
<ITEMS>2.02
<ITEMS>9.01
-->
<PRE>&lt;DOCUMENT&gt;
&lt;TYPE&gt;8-K
&lt;FILENAME&gt;body-8k.htm
&lt;DESCRIPTION&gt;CURRENT REPORT
&lt;/DOCUMENT&gt;
&lt;DOCUMENT&gt;
&lt;TYPE&gt;EX-99.1
&lt;FILENAME&gt;release.htm
&lt;DESCRIPTION&gt;PRESS RELEASE
&lt;/DOCUMENT&gt;
</PRE></HTML>"""

    items, documents = tf.parse_header(header)
    assert items == ["2.02", "9.01"]
    assert documents == [
        ("8-K", "body-8k.htm", "CURRENT REPORT"),
        ("EX-99.1", "release.htm", "PRESS RELEASE"),
    ]

    # The exhibit wins over the body, and that is the substantive choice:
    # Item 2.02 furnishes the release as an exhibit and the body typically
    # incorporates it by reference, so taking the body would retain a
    # cross-reference where the corpus needs prose with figures in it.
    assert tf.select_release(documents) == "release.htm"
    assert tf.select_release([("8-K", "body-8k.htm", "")]) == "body-8k.htm"

    # A filing with nothing takeable is REFUSED, never skipped: a filing
    # dropped without a record is a filing missing from a denominator.
    with pytest.raises(tf.TraceCorpusRefused, match="missing from a denominator"):
        tf.select_release([("GRAPHIC", "logo.jpg", "")])


def test_the_header_url_is_derived_and_never_guessed():
    assert tf.header_url("edgar/data/2064314/0001213900-26-093981.txt") == (
        "https://www.sec.gov/Archives/edgar/data/2064314/"
        "000121390026093981/0001213900-26-093981-index-headers.html")
    with pytest.raises(tf.TraceCorpusRefused, match="not a submission text path"):
        tf.header_url("edgar/data/2064314/index.html")


def test_the_endpoints_are_edgar_structured_not_screen_scraped():
    assert tf.daily_index_url(date(2026, 8, 27)) == (
        "https://www.sec.gov/Archives/edgar/daily-index/2026/QTR3/form.20260827.idx")
    assert tf.daily_index_url(date(2026, 2, 3)).endswith("QTR1/form.20260203.idx")
    assert tf.submissions_url("320193") == (
        "https://data.sec.gov/submissions/CIK0000320193.json")


def test_the_manifest_retains_raw_and_carries_the_non_evidentiary_stamp(tmp_path):
    """Extraction is destructive, so the response is kept beside the record.

    `corpora/us` learned this the hard way: `raw_bytes` was a number with
    nothing behind it until the pages were retained.
    """

    body = "<html><body>Third quarter results.</body></html>"
    f = tf.FetchedFiling(
        url="https://www.sec.gov/Archives/edgar/data/444444/000.../release.htm",
        cik="0000444444", company="SOMETHING ELSE CO",
        retrieved_at="2026-08-27T00:00:00+00:00",
        raw_bytes=len(body), digest=hashlib.sha256(body.encode()).hexdigest(),
        text=body, items="2.02,9.01", accession="0000444444-26-000001",
        scanned=37, candidates=161,
    )
    manifest = tf.write_manifest([f], root=tmp_path / "_trace_filings")
    text = manifest.read_text()
    assert text.startswith(f"# {tf.NON_EVIDENTIARY}")
    assert ("url\tcik\tcompany\taccession\titems\tretrieved_at\traw_bytes\t"
            "digest") in text
    assert f.digest in text
    # Every item is recorded, not only the one filtered on: a filing furnishing
    # 2.02 alongside 9.01 is a different object from one furnishing 2.02 alone.
    assert "2.02,9.01" in text
    # And the yield carries its denominator. A rate over items kept, with the
    # number examined unrecorded, is a rate nobody can reconstruct.
    assert "37 of 161" in text
    kept = (tmp_path / "_trace_filings" / "_raw" / f"{f.stem}.html").read_text()
    assert kept == body
    # Re-extraction: the retained response reproduces the recorded digest.
    assert hashlib.sha256(kept.encode()).hexdigest() == f.digest
    # And the whole store is fenced.
    from fntn.scanner.corpusio import corpus_documents, is_fenced_path
    assert is_fenced_path(manifest.parent)
    assert corpus_documents(manifest.parent) == []


# ---------------------------------------------------------------------------
# The derived clip floor (§13 rows 29 and 30).
#
# The clip was a chosen constant; §0.11 withdrew the number and replaced it
# with a derivation.  These tests exercise the three refusals first, because
# under the register as it stands the derivation REFUSES for every market and
# the refusal is the product.
# ---------------------------------------------------------------------------

from fntn.scanner.records import Refusal
from fntn.scanner.sizing import ClipFloor, FixedCost, cost_at, derive_clip_floor


def test_the_floor_refuses_when_row_29_is_unset():
    """Row 29 is the one free parameter the derivation cannot eliminate."""

    cost = FixedCost("US", "USD", 6.00, 0.0, "operator_model")
    r = derive_clip_floor(cost, None)
    assert isinstance(r, Refusal)
    assert r.code == "clip_floor_tolerance_unset"
    assert r.surface == "sizing"
    assert codes.ALL_CODES[r.code].refuse_to_score
    # A refusal to score, not a size of zero. The distinction is the point.
    assert "UNDETERMINED" in r.summary and "not a size of zero" in r.summary


def test_the_floor_refuses_when_row_1_is_unset_for_the_market():
    """Row 1 runs first because every break-even denominator inherits it."""

    for cost in (
        FixedCost("UK", "GBP", None, 61.4),
        FixedCost("UK", "GBP", 1.00, None),
        FixedCost("UK", "GBP", None, None),
    ):
        r = derive_clip_floor(cost, 10.0)
        assert isinstance(r, Refusal) and r.code == "clip_floor_cost_unset"
        assert codes.ALL_CODES[r.code].refuse_to_score
    # The missing field is named, not merely counted.
    r = derive_clip_floor(FixedCost("UK", "GBP", None, 61.4), 10.0)
    assert "absolute_round_trip" in r.summary


def test_no_size_satisfies_a_tolerance_below_the_proportional_share():
    """The UK result, and it is a measured fact rather than a missing input.

    Stamp duty is a percentage. A percentage does not decay as the position
    grows, so where it alone meets the tolerance there is no floor to derive
    and returning a very large number instead would say the market was
    reachable at a price.
    """

    uk = FixedCost("UK Main Market", "GBP", 1.00, 61.4, "row1_provisional")
    for tolerance in (2.0, 10.0, 25.0, 50.0, 61.0, 61.4):
        r = derive_clip_floor(uk, tolerance)
        assert isinstance(r, Refusal), tolerance
        assert r.code == "clip_floor_unreachable_at_any_size"
        # NOT a refusal to score: nothing is missing.
        assert not codes.ALL_CODES[r.code].refuse_to_score
    assert "does not fall as the position grows" in r.summary
    # Above it, a floor exists again.
    above = derive_clip_floor(uk, 62.0)
    assert isinstance(above, ClipFloor) and above.floor == pytest.approx(16666.7, rel=1e-3)


def test_stamp_duty_alone_excludes_uk_main_market_below_50_bp_with_certainty():
    """The robust half of the claim, separated from the provisional half.

    Stamp duty is 50 bp by statute and does not depend on row 1's three open
    gaps. The 61.4 bp total does. So one claim survives row 1 closing any way
    at all and the other does not, and they are asserted separately.
    """

    statutory = FixedCost("UK Main Market", "GBP", 0.0, 50.0, "statutory")
    for tolerance in (2.0, 10.0, 25.0, 49.9, 50.0):
        r = derive_clip_floor(statutory, tolerance)
        assert isinstance(r, Refusal)
        assert r.code == "clip_floor_unreachable_at_any_size"


def test_the_us_floor_derives_and_falls_as_the_tolerance_rises():
    """Two fixed minimums applied twice: the cost decays, so a floor exists."""

    us = FixedCost("US", "USD", 6.00, 0.0, "operator_model")
    floors = {}
    for tolerance in (2.0, 5.0, 10.0, 20.0):
        r = derive_clip_floor(us, tolerance)
        assert isinstance(r, ClipFloor)
        floors[tolerance] = r.floor
    assert floors == {2.0: 30000.0, 5.0: 12000.0, 10.0: 6000.0, 20.0: 3000.0}
    # Monotone: a looser tolerance never demands a larger position.
    assert list(floors.values()) == sorted(floors.values(), reverse=True)
    # And the floor is the size at which the cost EQUALS the tolerance.
    assert cost_at(us, floors[10.0]) == pytest.approx(10.0)


def test_a_derived_floor_carries_the_provenance_of_the_cost_it_came_from():
    """A number that has lost its provenance gets quoted under a hash it was
    never taken under, which is the defect §13 rows 19 to 21b are annotated
    against."""

    us = FixedCost("US", "USD", 6.00, 0.0, "row1_provisional")
    r = derive_clip_floor(us, 10.0)
    assert r.provenance == "row1_provisional"
    assert r.cost is us and r.tolerance_bps == 10.0


def test_the_two_recorded_us_readings_imply_a_proportional_term():
    """The disagreement this phase found, asserted so it cannot be lost.

    §13 row 1 records ~19 bp at about USD 3,200 and ~3 bp at USD 64,000. The
    operator's model, USD 1.00 commission and USD 2.00 FX each applied twice,
    reproduces the first and gives 0.94 bp for the second. The residual is the
    signature of a term that does NOT decay.
    """

    stated = FixedCost("US", "USD", 6.00, 0.0)
    assert cost_at(stated, 3200) == pytest.approx(18.75)
    assert cost_at(stated, 64000) == pytest.approx(0.9375)

    # Solve the two recorded points for (absolute, proportional).
    absolute = (19.0 - 3.0) / (1e4 * (1 / 3200 - 1 / 64000))
    proportional = 3.0 - 1e4 * absolute / 64000
    assert absolute == pytest.approx(5.39, abs=0.01)
    assert proportional == pytest.approx(2.16, abs=0.01)

    implied = FixedCost("US", "USD", absolute, proportional)
    assert cost_at(implied, 3200) == pytest.approx(19.0)
    assert cost_at(implied, 64000) == pytest.approx(3.0)

    # And the consequence that matters: under the implied model a 2 bp
    # tolerance is unreachable in the US too.
    r = derive_clip_floor(implied, 2.0)
    assert isinstance(r, Refusal) and r.code == "clip_floor_unreachable_at_any_size"


# ---------------------------------------------------------------------------
# The 1e residual: a regime change, not a mystery term.
# ---------------------------------------------------------------------------

from fntn.scanner.sizing import (
    US_FIXED, US_TIERED, hard_floor_bps, minimum_share_price,
    rate_regime_from, us_clip_floor, us_round_trip_bps,
)


def test_one_model_fitted_to_one_reading_predicts_the_other():
    """The test that makes this a reconciliation rather than a fit.

    The share price is solved from the USD 64,000 reading alone. Hitting that
    reading is therefore not evidence. **The evidence is the other point**: the
    model then predicts ~18.8 bp at USD 3,200, against the ~19 bp §13 row 1
    records, having never been shown it.
    """

    for schedule, implied in ((US_FIXED, 43.79), (US_TIERED, 31.16)):
        assert us_round_trip_bps(schedule, 64000, implied) == pytest.approx(3.0, abs=0.01)
        predicted = us_round_trip_bps(schedule, 3200, implied)
        assert predicted == pytest.approx(18.85, abs=0.1)
        assert abs(predicted - 19.0) < 0.2


def test_the_residual_is_the_per_share_commission_crossing_its_minimum():
    """Why one linear model could not straddle the two readings.

    At USD 3,200 the per-share commission is well under the USD 1.00 order
    minimum, so it behaves as a fixed charge and decays. At USD 64,000 the rate
    binds and it does not decay at all. A single (absolute, proportional) pair
    fitted across that boundary splits the difference, which is what produced
    the 2.16 bp nobody could name.
    """

    p = 43.79
    boundary = rate_regime_from(US_FIXED, p)
    assert 3200 < boundary < 64000
    assert US_FIXED.per_share * 3200 / p < US_FIXED.order_minimum
    assert US_FIXED.per_share * 64000 / p > US_FIXED.order_minimum
    # The asymptote the fit was groping at.
    assert hard_floor_bps(US_FIXED, p) == pytest.approx(2.375, abs=0.01)


def test_the_us_hard_floor_is_a_function_of_share_price_not_a_constant():
    """The finding: a tight tolerance excludes low-priced US stocks at ANY size,
    in the same way and for the same reason stamp duty excludes UK Main."""

    assert hard_floor_bps(US_FIXED, 100) == pytest.approx(1.04)
    assert hard_floor_bps(US_FIXED, 10) == pytest.approx(10.4)
    assert hard_floor_bps(US_FIXED, 2) == pytest.approx(52.0)
    # Halving the price doubles the floor. It is 1/p, exactly.
    assert hard_floor_bps(US_FIXED, 20) == pytest.approx(2 * hard_floor_bps(US_FIXED, 40))
    # Minimum share price inverts it, and tiered is ~30% cheaper.
    assert minimum_share_price(US_FIXED, 2.0) == pytest.approx(52.0)
    assert minimum_share_price(US_TIERED, 2.0) == pytest.approx(37.0)
    assert minimum_share_price(US_TIERED, 5.0) / minimum_share_price(US_FIXED, 5.0) \
        == pytest.approx(74 / 104, rel=1e-9)


def test_unreachable_fires_for_the_us_below_the_hard_floor(): 
    """1e's requirement: the distinction from a refusal to score must survive."""

    r = us_clip_floor(US_FIXED, 10.0, 2.0)        # floor 10.4 bp > 2 bp
    assert isinstance(r, Refusal)
    assert r.code == "clip_floor_unreachable_at_any_size"
    assert not codes.ALL_CODES[r.code].refuse_to_score
    assert "USD 10 per share" in r.summary
    # Above the hard floor a floor exists again.
    ok = us_clip_floor(US_FIXED, 10.0, 20.0)
    assert isinstance(ok, ClipFloor) and ok.floor > 0
    assert us_round_trip_bps(US_FIXED, ok.floor, 10.0) == pytest.approx(20.0, abs=0.01)
    # And an unset tolerance is still the OTHER refusal.
    assert us_clip_floor(US_FIXED, 10.0, None).code == "clip_floor_tolerance_unset"


def test_the_election_moves_the_us_hard_floor_by_about_thirty_percent():
    """Row 1's tiered-or-fixed gap was a convenience question. It is now a
    universe question: 100/p against 70/p before clearing charges."""

    for p in (10.0, 25.0, 50.0, 100.0):
        ratio = hard_floor_bps(US_TIERED, p) / hard_floor_bps(US_FIXED, p)
        assert ratio == pytest.approx(74 / 104, rel=1e-9)
        assert 0.70 < ratio < 0.72


def test_the_model_pin_is_a_registered_field_and_has_no_default_anywhere():
    """B15. §13 row 39 said this was already true. It was not.

    The pin lived as a default string in `clients.py` and a second copy as an
    argparse default in `cli.py`, so the model every future sweep ran under
    could be changed without moving a hash or leaving a row in
    `docs/REGISTRATION_HISTORY.md`. That is the defect row 39's open half is
    about, reached through the front door rather than through an alias.

    Three things are held here and each failed before the repair: the field
    exists and is hashed, an absent pin is a named gap rather than a default,
    and neither module carries a fallback the registration does not cover.
    """

    import dataclasses
    import re

    from fntn.scanner.params import Registration

    # One: it is a field, and it reaches the hash.
    names = {f.name for f in dataclasses.fields(Registration)}
    assert "agent_model" in names
    a = _complete_registration(agent_model="claude-a")
    b = _complete_registration(agent_model="claude-b")
    assert a.hash() != b.hash(), "a pin that does not move the hash is not registered"

    # Two: absent is a gap with a reason, never a default.
    gaps = _complete_registration(agent_model=None).missing()
    assert any("agent_model" in g and "§13 row 39" in g for g in gaps)

    # Three: no second copy of the pin anywhere in the package. A default in
    # the code is a pin that moves with nothing on the record.
    root = Path(__file__).resolve().parents[1] / "src" / "fntn" / "scanner"
    for path in root.glob("*.py"):
        body = path.read_text(encoding="utf-8")
        # Comments and docstrings may name an identifier; assignments may not.
        for line in body.splitlines():
            code = line.split("#", 1)[0]
            assert not re.search(r"=\s*\"claude-[a-z0-9.\-]+\"", code), (
                f"{path.name} assigns a model identifier: {line.strip()!r}. The "
                "pin is registered (§13 row 39) and a default here is a copy "
                "of it that no hash covers."
            )


def test_the_spend_refuses_to_score_a_model_it_has_no_rate_for():
    """Rule 3, applied to the one quantity the operator actually spends.

    An unknown rate is not a small rate. A cost guard that treated a missing
    price as zero would wave through exactly the sweep it exists to stop, and
    it would do it silently.
    """

    from fntn.scanner.clients import Spend

    known = Spend.of("claude-sonnet-5", 1, 1_000_000, 1_000_000, 0, 0, True)
    assert known.usd == pytest.approx(12.00)

    unknown = Spend.of("claude-not-in-the-table", 1, 1_000_000, 0, 0, 0, True)
    assert unknown.usd is None
    assert "NOT SCORED" in unknown.render()
    assert "is not zero" in unknown.render()

    # A usage block missing a billed counter makes the figure a LOWER BOUND and
    # says so, rather than reporting a smaller number as though it were the
    # measurement.
    partial = Spend.of("claude-sonnet-5", 1, 1_000_000, 0, 0, 0, False)
    assert "LOWER BOUND" in partial.render()


def test_the_cost_guard_stops_the_whole_sweep_and_never_truncates_it():
    """B1's guard. A stop, and deliberately not a partial book.

    The abort is raised from inside the gather loop, so the control arm has not
    been drawn and nothing has reached the ledger. A sweep over one family of
    three, reported as a sweep, would put a partial population under §7.1's
    headline with nothing on the record saying so.
    """

    from fntn.scanner.cli import CostCeilingExceeded, _cost_guard

    class _Client:
        model = "claude-sonnet-5"

        def spend(self):
            from fntn.scanner.clients import Spend
            return Spend.of(self.model, 1, 1_000_000, 200_000, 0, 0, True)

    # 1M in + 200k out at Sonnet 5 list is USD 4.00 for one family; three
    # families project to 12.00.
    guard = _cost_guard(_Client(), ceiling_usd=4.0)
    with pytest.raises(CostCeilingExceeded, match="exceeds the ceiling"):
        guard(0, 3)

    # Within the ceiling it returns, and it fires only after the FIRST corpus:
    # a guard that re-projected after every family would keep paying to
    # re-learn what it already measured.
    assert _cost_guard(_Client(), ceiling_usd=20.0)(0, 3) is None
    assert _cost_guard(_Client(), ceiling_usd=0.01)(1, 3) is None

    # A ceiling of zero disables the guard, and that is a decision the operator
    # takes explicitly rather than a default that happens to be off.
    assert _cost_guard(_Client(), ceiling_usd=0.0) is None


def test_a_payload_element_the_schema_does_not_describe_is_counted_not_crashed():
    """B16. The first live sweep raised `AttributeError` in the loader.

    **A forced tool call is not a validated tool call.** `tool_choice` makes the
    model call the tool; it does not make the arguments conform, and `strict` is
    not set. The clerk returned a bare string in the proposals array and the
    loader called `.get` on it, part-way through the second of three families,
    losing the remaining families and the money already spent on them.

    Three things are held here and each failed before the repair: the sweep
    survives, the element is counted with a registered reason code, and it is
    NOT repaired into a proposal by guessing which field it was meant to be.
    """

    from fntn.scanner.discovery import Corpus, ProposalCache, raw_payloads, sweep
    from fntn.scanner.fences import QueryFence
    from fntn.scanner.records import Partition

    class _Client:
        def complete(self, system, user, schema):
            return {"proposals": [
                "a bare string the schema does not describe",
                {"event_definition": "clusters of same-day director purchases",
                 "measured_on_intention": "US small caps",
                 "event_class": "insider_dealing",
                 "source_ref": "doc-1"},
                None,
                42,
            ]}

    result = sweep(
        _Client(),
        Corpus("c1", Partition.EXTERNAL, ["doc-1"]),
        QueryFence(),
        ProposalCache(),
    )

    # One proposal survives; three elements are counted off-schema, with the
    # type named so the refusal says what actually arrived.
    assert len(result.proposals) == 1
    assert result.off_schema == [(0, "str"), (2, "NoneType"), (3, "int")]

    # NOT repaired. A bare string could be coaxed into `event_definition`, and
    # that is the loader doing the clerk's work on material the clerk did not
    # put in a field.
    assert all("bare string" not in p.event_definition for p in result.proposals)

    # The authority fence sees only what it can inspect, and a non-object
    # carries no field for it to inspect.
    assert len(raw_payloads({"proposals": ["x", {"a": 1}]})) == 1


def test_the_off_schema_code_is_non_positional_and_row_23_does_not_move():
    """§13 row 23 counts abort positions, so the panel may not silently grow.

    The code is emitted before a subject exists: the element never became a
    proposal, so it never entered intake and there is no position at which it
    could have aborted. Position 1 would report a parse failure as the first
    check refusing; inserting it anywhere would make every abort position
    recorded before today incomparable with every one recorded after.
    """

    from fntn.scanner.codes import (
        ALL_CODES,
        INTAKE_NON_POSITIONAL,
        INTAKE_ORDER,
    )

    assert "agent_payload_off_schema" in ALL_CODES
    assert "agent_payload_off_schema" in INTAKE_NON_POSITIONAL
    assert "agent_payload_off_schema" not in INTAKE_ORDER
    # The panel is twelve positions and this batch did not change that.
    assert len(INTAKE_ORDER) == 12


def test_a_string_payload_is_one_refusal_and_not_one_per_character():
    """B16's second half, and the one that matters for the denominator.

    On the first live sweep two of three families returned `proposals` as a
    JSON *string*. A string is iterable, so reading it element-wise walked its
    characters: 5,607 and 2,869 refusals from two malformed replies, a funnel
    reporting **8,484 proposals raised** where four mechanisms had been
    located, and a reason-code distribution in which one code held 99.9% of the
    mass.

    *Rule 5 says counting is mechanical because intent flatters the
    denominator.* **Nothing intended that denominator and it was flattered
    anyway**, which is the case the rule is weakest against and the reason the
    two failures are counted separately rather than by one tolerant branch.
    """

    from fntn.scanner.discovery import Corpus, ProposalCache, raw_payloads, sweep
    from fntn.scanner.fences import QueryFence
    from fntn.scanner.records import Partition

    class _StringPayload:
        def complete(self, system, user, schema):
            return {"proposals": "[{\"event_definition\": \"x\"}]"}

    result = sweep(
        _StringPayload(),
        Corpus("c1", Partition.EXTERNAL, ["doc-1"]),
        QueryFence(),
        ProposalCache(),
    )

    assert result.proposals == []
    # ONE fact about ONE call, with the type and the length recorded so the
    # refusal says what arrived rather than how many characters it had.
    assert result.payload_not_a_list == ("str", 27)
    assert result.off_schema == [], (
        "a non-array payload must not also produce per-element refusals: that "
        "is the character-counting defect arriving by a second route"
    )

    # The authority fence is handed nothing rather than a list of characters.
    assert raw_payloads({"proposals": "not a list"}) == []


def test_the_per_family_table_never_pools_the_two_arms():
    """§13 row 20's whole purpose is a comparison.

    The control arm is drawn from the grid and carries the first registered
    corpus's id by construction, so keying it on that id would file random
    draws under a family that did not produce them. Pooling the arms in the one
    table that exists to keep them apart destroys the only instrument that can
    refute the discovery layer.
    """

    from fntn.scanner.discovery import Corpus as _C, GridCell as _G
    from fntn.scanner.run import ScanConfig as _Cfg, scan as _scan

    class _Client:
        def complete(self, system, user, schema):
            return {"proposals": [{
                "event_definition": "clusters of same-day director purchases",
                "measured_on_intention": "US small caps",
                "event_class": "insider_dealing",
                "source_ref": "doc-1",
            }]}

    ledger = Ledger(parameter_hash="perfamily")
    result = _scan(
        _Client(),
        [_C("fam-a", Partition.EXTERNAL, ["d1"]), _C("fam-b", Partition.EXTERNAL, ["d2"])],
        [_G("insider_dealing", "pop", "a mechanism")],
        _Cfg(parameter_hash="perfamily", audit_fraction=1.0,
             control_arm_ratio=1.0, control_arm_seed=1),
        ledger,
    )

    assert "control_arm" in result.per_family, (
        "the control arm has no row, so the comparison the sweep exists to "
        "make cannot be read off the table"
    )
    assert set(result.per_family) == {"fam-a", "fam-b", "control_arm"}
    # Every proposal is in exactly one row, and the rows sum to the funnel.
    assert sum(r["raised"] for r in result.per_family.values()) == result.proposed
    rendered = result.render(ledger)
    assert "NEVER pooled" in rendered
    ledger.close()


def test_the_delisting_register_never_sums_deregistrations_with_delistings():
    """A Form 15 is deregistration, not delisting, and conflating them flatters.

    Counting Form 15s into the missing set would inflate the denominator of
    names the archive is missing, which makes the survivorship bound look
    tighter than it is. **A bound that errs towards comfort is worse than no
    bound**, so the two are recorded under their own form codes and the
    accessors keep them apart.
    """

    from fntn.data.delistings import Register, parse_index

    index = """Description:           Quarterly Index

Form Type   Company Name                                       CIK         Date Filed  File Name
---------------------------------------------------------------------------------------------------
25          ACME CORP                                          0000320193  2023-02-01  edgar/data/320193/a.txt
25-NSE      BOREALIS MINING PLC                                0000222222  2023-02-02  edgar/data/222222/b.txt
25-NSE      ACME CORP                                          0000320193  2023-02-03  edgar/data/320193/c.txt
15-12G      QUIET HOLDINGS INC                                 0000333333  2023-02-04  edgar/data/333333/d.txt
15F-12B     FOREIGN ISSUER SA                                  0000444444  2023-02-05  edgar/data/444444/e.txt
8-K         NOT RELEVANT CO                                    0000555555  2023-02-06  edgar/data/555555/f.txt
"""

    events = parse_index(index)
    r = Register(events=events, quarters=[(2023, 1)], fetch_log=[])

    assert len(r.delistings) == 3
    assert len(r.deregistrations) == 2
    assert r.by_form() == {"25": 1, "25-NSE": 2, "15-12G": 1, "15F-12B": 1}

    # ISSUERS, not filings. ACME filed a 25 and a 25-NSE; it is one missing
    # name, and the missing-set denominator is a count of names.
    assert r.distinct_delisted_ciks() == 2

    # `25` is a prefix of `25-NSE`, so the form match is EXACT: a prefix match
    # would count every exchange notification twice, once as itself and once as
    # an issuer filing that never happened.
    from fntn.data.delistings import DELISTING_FORMS
    assert set(DELISTING_FORMS) == {"25", "25-NSE"}
    assert [e.form for e in r.delistings].count("25") == 1


def test_the_coverage_fraction_refuses_rather_than_assuming_an_archive():
    """Rule 3, on the number this whole register exists to produce.

    A coverage fraction computed against an assumed archive size is the exact
    defect the register exists to prevent, wearing the register's own clothes.
    There is no archive, so there is no N, so there is no fraction.
    """

    from fntn.data.delistings import Event, Register

    r = Register(
        events=[Event("25", "1", "A", "2023-01-02", "p.txt"),
                Event("25-NSE", "2", "B", "2023-01-03", "q.txt")],
        quarters=[(2023, 1)], fetch_log=[],
    )
    assert r.coverage_fraction(None) is None
    assert r.coverage_fraction(0) is None
    # 8 covered names against 2 missing is 8/10.
    assert r.coverage_fraction(8) == pytest.approx(0.8)


def test_the_span_is_inclusive_at_both_ends_and_a_reversed_span_refuses():
    """A partial quarter is still a quarter that must be read.

    Dropping it would leave a hole in the missing set exactly at the span
    boundary, which is where a coverage claim is least defensible.
    """

    from datetime import date as _date

    from fntn.data.delistings import TraceCorpusRefused, quarters_between

    assert quarters_between(_date(2023, 1, 1), _date(2023, 1, 1)) == [(2023, 1)]
    assert quarters_between(_date(2023, 3, 31), _date(2023, 4, 1)) == [
        (2023, 1), (2023, 2)]
    assert len(quarters_between(_date(2023, 1, 1), _date(2026, 8, 27))) == 15
    with pytest.raises(TraceCorpusRefused, match="closes .* before it opens"):
        quarters_between(_date(2026, 1, 1), _date(2023, 1, 1))


def test_the_report_and_the_sweep_do_not_share_a_label_for_different_counts():
    """B18. Two numbers under one name is the P105 defect in a word.

    `ScanResult.proposed` counts EMISSIONS: proposals, plus payload elements
    the schema does not describe, plus calls that returned no array at all.
    The report counts ROWS IN THE PROPOSAL TABLE, and an emission that never
    became a proposal has a refusal and no proposal row. On the run of record
    the two read 13 and 12.

    Both are defensible. **They may not share a label**, because a denominator
    that means one thing in one report and another in the next is unusable in
    either.
    """

    from fntn.scanner import report as report_mod

    source = Path(report_mod.__file__).read_text(encoding="utf-8")
    assert "proposals recorded in the ledger" in source
    # And the sweep's own funnel keeps its own wording, which is the one that
    # counts emissions.
    from fntn.scanner import run as run_mod
    assert "proposals raised" in Path(run_mod.__file__).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The 28 August repairs. One test per finding, each named for what it would
# have caught rather than for the function it calls.
# ---------------------------------------------------------------------------


def test_the_clerk_is_given_the_table_it_is_told_to_classify_against():
    """B5. The prompt said *the fixed table* and the table was never sent.

    `event_class` was a free string, the user message carried the corpus and
    nothing else, and `STREAM_TABLE` lived in `screen.py` where no call could
    reach it. So `unclassified` was not the fallback branch: it was the only
    branch reachable on the instructions given, and the run of record's
    six-of-six intake kill followed by construction.
    """

    seen = {}

    class Recorder:
        def complete(self, system, user, schema):
            seen["user"] = json.loads(user)
            seen["schema"] = schema
            return {"proposals": []}

    sweep(Recorder(), Corpus("c", Partition.EXTERNAL, ["d"]), QueryFence(),
          ProposalCache(), now=NOW, classes=["buyback", "earnings_event"])

    # Supplied.
    assert seen["user"]["event_class_table"] == [
        "buyback", "earnings_event", UNCLASSIFIED
    ]
    # And enforced, which is the half a prompt alone does not buy.
    enum = (seen["schema"]["properties"]["proposals"]["items"]
            ["properties"]["event_class"]["enum"])
    assert enum == ["buyback", "earnings_event", UNCLASSIFIED]


def test_the_permitted_vocabulary_always_admits_unclassified():
    """P51's escape hatch may not be closed by a registration that forgot it.

    Refusing on unclassified would make the table's current contents a ceiling
    on what the system can ever investigate, which is the endogeneity §3.6.6
    exists to contain, hard-coded into the machinery instead.
    """

    for classes in ([], ["buyback"], ["a", "b", "c"]):
        enum = (proposal_schema(classes)["properties"]["proposals"]["items"]
                ["properties"]["event_class"]["enum"])
        assert enum[-1] == UNCLASSIFIED
        assert enum.count(UNCLASSIFIED) == 1


def test_unclassified_reaches_the_operator_instead_of_dying_at_intake():
    """B6. `stream_unmapped_pending_operator` had never been emitted.

    It sat in the run report's defined-but-never-emitted list, which is §9.4's
    own failure class -- a rule that is wrong because nothing ever reached it --
    inside the layer §9.4 is aimed at. Intake point 9 was what nothing got past.
    """

    from fntn.scanner.ingest import build_intake_checks

    checks = build_intake_checks()

    class Ctx:
        proposal = Proposal(
            event_definition="a mechanism",
            measured_on_intention="US common equities",
            event_class=UNCLASSIFIED,
            source_ref="ref",
            source_partition=Partition.EXTERNAL,
        )
        exclusivity_available = {"buyback": "cross_market"}

    assert checks["scoring_mode_unsatisfiable"](Ctx()) is None

    # A class that is genuinely undeclared is still refused: the repair is
    # narrow, and it does not open the check it moves one case out of.
    class Other(Ctx):
        proposal = Proposal(
            event_definition="a mechanism",
            measured_on_intention="US common equities",
            event_class="index_reconstitution",
            source_ref="ref",
            source_partition=Partition.EXTERNAL,
        )

    refusal = checks["scoring_mode_unsatisfiable"](Other())
    assert refusal is not None and refusal[0] == "scoring_mode_unsatisfiable"


def test_registration_refuses_a_directive_with_no_registered_sign():
    """§3.6.8 step 4: any part missing, no observation. The sign was the part
    nothing refused on.

    `register` blocked on delta_min, the pre-mortem and the literature search
    and let a directive through with no sign, so the direction could be chosen
    once the answer was known -- the endogeneity P57 replaced sign-against-zero
    to close, arriving through the gap where the check should have been.
    """

    blocking = register(
        _directive(),
        RegistrationInputs(
            delta_min=40.0,
            pre_mortem=PreMortem("confound", True, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    assert [r.code for r in blocking] == ["registered_sign_absent"]


def test_a_sign_outside_minus_one_and_plus_one_is_not_a_sign():
    blocking = register(
        _directive(),
        RegistrationInputs(
            delta_min=40.0,
            registered_sign=0,
            pre_mortem=PreMortem("confound", True, "operator", True),
            literature_search_ref="ref",
        ),
        25.0,
        NOW,
    )
    assert [r.code for r in blocking] == ["registered_sign_absent"]


def test_the_lens_refuses_a_pointer_instead_of_returning_nine_unscorables():
    """C1. Nine unscorables was never a reading.

    Nothing in `src/` constructs a Candidate from a proposal; the schema has no
    column for seven criteria; and rule 3 discards whole any proposal stating an
    effect size or a horizon, which are the other two. The lens can return
    nothing else on a pointer at any sample size, and reporting that as a result
    put a category error in a table where it read as a finding about mechanisms.
    """

    from fntn.scanner.achievability import Candidate, LensNotApplicable, score

    pointer = Candidate("m-1", origin="agent", evidence_tier="pointer")
    try:
        score(pointer, tolerance_bps=10.0, delta_min_floor_bps=15.7,
              smallest_position_usd=2419.0)
    except LensNotApplicable as exc:
        assert "pointer" in str(exc)
    else:
        raise AssertionError("the lens scored a pointer")


def test_the_lens_still_scores_an_item_that_declares():
    from fntn.scanner.achievability import Candidate, Result, score

    item = Candidate(
        "m-2", origin="operator", long_only=True, us_listed=True,
        min_share_price_usd=25.0, median_daily_notional_usd=5_000_000,
        survives_to_next_open=True, claimed_effect_bps=40.0,
        holding_period_sessions=21, obtainable_without_purchase=True,
    )
    reading = score(item, tolerance_bps=10.0, delta_min_floor_bps=15.7,
                    smallest_position_usd=2419.0)
    assert reading.met == 8
    assert reading.unscorable == ["backtestable"]


def test_the_registered_classes_are_the_ones_the_sweep_is_given():
    """Row 22 and the enum are one object, not two copies of one.

    A second place the vocabulary lives is a second place it can diverge, which
    is the defect `rulebook_stopwords`, `lexicon` and the intake budget were all
    re-stamped to close.
    """

    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    declared = sorted(c.event_class for c in reg.discoverable_classes)
    enum = (proposal_schema(declared)["properties"]["proposals"]["items"]
            ["properties"]["event_class"]["enum"])
    assert enum == declared + [UNCLASSIFIED]


def test_every_stream_table_class_is_declared_discoverable():
    """§0 decision, 28 August 2026.

    Four classes were funnel-reachable and discovery-unreachable, with nothing
    on the register saying that had been chosen. A proposal correctly classified
    to one of them died at intake point 9 while no control draw could, which is
    the arm asymmetry that made §13 row 19's verdict uncomputable.
    """

    from fntn.scanner.screen import STREAM_TABLE

    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    declared = {c.event_class for c in reg.discoverable_classes}
    assert declared == set(STREAM_TABLE)


def test_the_prompt_and_schema_digests_are_typed():
    """A digest that cannot be told from a registration hash is a defect.

    `SCHEMA_PREFIX` established the pattern and the repository sweeps its own
    documents for the bare shape.
    """

    assert prompt_sha().startswith("prompt:")
    assert schema_sha().startswith("proposal_schema:")


def test_the_registration_pins_the_prompt_the_code_actually_sends():
    """B15's defect in a larger field: the prompt moved nothing when it moved.

    A prompt edit changed what every future sweep produced while moving no hash
    and leaving no row. This is what says the registered digest and the live
    prompt have not drifted apart.
    """

    reg = Registration.load(REPO_ROOT / REGISTRATION_FILE)
    assert reg.agent_prompt_sha == prompt_sha()
    assert reg.proposal_schema_sha == schema_sha()
    assert reg.structured_outputs_strict is True


# ---------------------------------------------------------------------------
# §13 row 12. The three tests are conjunctive and a word match cannot do them.
# ---------------------------------------------------------------------------

def _form4(code="P", ad="A", shares=1000, price="25.00", director="1",
           officer="0", ten="0"):
    return f"""<ownershipDocument>
  <periodOfReport>2026-08-03</periodOfReport>
  <issuer><issuerCik>0000320193</issuerCik></issuer>
  <reportingOwner><reportingOwnerRelationship>
    <isDirector>{director}</isDirector><isOfficer>{officer}</isOfficer>
    <isTenPercentOwner>{ten}</isTenPercentOwner>
  </reportingOwnerRelationship></reportingOwner>
  <nonDerivativeTransaction>
    <transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
    <transactionAmounts>
      <transactionShares><value>{shares}</value></transactionShares>
      <transactionPricePerShare><value>{price}</value></transactionPricePerShare>
      <transactionAcquiredDisposedCode><value>{ad}</value></transactionAcquiredDisposedCode>
    </transactionAmounts>
  </nonDerivativeTransaction>
</ownershipDocument>"""


def test_row12_a_clean_director_open_market_purchase_qualifies():
    from fntn.scanner.row12 import read_form4
    r = read_form4(_form4())
    assert (r.test1_net_increase, r.test2_open_market, r.test3_qualifying_filer) == (True, True, True)
    assert r.qualifies and r.price_usd == 25.0


def test_row12_the_three_filings_that_pass_a_word_match_and_carry_no_information():
    """The trace over one week's RNS flow found these; P30 is written from them."""

    from fntn.scanner.row12 import read_form4

    # A scheme award: shares acquired, and it is compensation, not a purchase.
    award = read_form4(_form4(code="A"))
    assert award.test1_net_increase and not award.test2_open_market
    assert not award.qualifies

    # An option exercise: an acquisition leg, and no view expressed.
    exercise = read_form4(_form4(code="M"))
    assert not exercise.qualifies

    # A ten-per-cent owner who is neither director nor officer. The literature
    # finds abnormal returns for insider purchases and none for large holders.
    holder = read_form4(_form4(director="0", officer="0", ten="1"))
    assert holder.test1_net_increase and holder.test2_open_market
    assert not holder.test3_qualifying_filer and not holder.qualifies


def test_row12_a_disposal_is_not_a_net_increase():
    from fntn.scanner.row12 import read_form4
    assert not read_form4(_form4(ad="D")).test1_net_increase


def test_row12_an_absent_price_is_not_a_price_below_the_floor():
    """A refusal, not a failure: the two are different claims about a filing."""

    from fntn.scanner.row12 import read_form4
    xml = _form4().replace(
        "<transactionPricePerShare><value>25.00</value></transactionPricePerShare>", "")
    r = read_form4(xml)
    assert r.price_usd is None
    assert r.clears_price_floor() is None
    assert read_form4(_form4(price="3.00")).clears_price_floor() is False


def test_row12_reports_every_denominator_and_refuses_the_liquidity_leg():
    from fntn.scanner.row12 import measure, read_form4
    readings = [read_form4(_form4()), read_form4(_form4(code="A")),
                read_form4(_form4(director="0", officer="0", ten="1")),
                read_form4(_form4(price="3.00"))]
    m = measure(readings)
    assert m.filings == 4 and m.qualifying == 2       # clean, and the cheap one
    assert m.price_cleared == 1                        # only the clean one clears
    text = m.render()
    assert "REFUSED, not estimated" in text
    assert "UPPER BOUND" in text
    assert "absent is NOT below" in text


def test_row12_refuses_a_rate_over_an_empty_set():
    from fntn.scanner.row12 import measure
    m = measure([])
    assert m.qualifying_rate is None
    assert "not a rate" in m.render()


def test_form_rows_is_form_agnostic_and_eight_k_rows_is_unchanged():
    """Generalised for §13 row 12 without moving step 4's population."""

    from fntn.scanner.trace_filings import eight_k_rows, form_rows

    index = (
        "Form Type  Company Name  CIK  Date Filed  File Name\n"
        "-------------------------------------------------\n"
        "8-K         Acme Corp                 320193 2026-08-03 edgar/data/320193/a.txt\n"
        "8-K/A       Acme Corp                 320193 2026-08-03 edgar/data/320193/b.txt\n"
        "4           Acme Corp                 320193 2026-08-03 edgar/data/320193/c.txt\n"
    )
    assert [r[2] for r in eight_k_rows(index)] == ["edgar/data/320193/a.txt"]
    assert [r[2] for r in form_rows(index, "4")] == ["edgar/data/320193/c.txt"]
    # The amendment exclusion is a property of the exact match, not of 8-K.
    assert form_rows(index, "8-K/A")[0][2] == "edgar/data/320193/b.txt"


def test_the_ownership_document_is_lifted_out_of_a_full_submission():
    from fntn.scanner.trace_filings import extract_ownership_document
    sub = ("<SEC-DOCUMENT>header noise\n<ownershipDocument><x/></ownershipDocument>\n"
           "<TYPE>GRAPHIC more noise")
    assert extract_ownership_document(sub) == "<ownershipDocument><x/></ownershipDocument>"


def test_a_submission_with_no_ownership_document_is_skipped_not_failed():
    """A paper filing and a PDF primary both land here, and neither is a defect."""

    from fntn.scanner.trace_filings import extract_ownership_document
    assert extract_ownership_document("<SEC-DOCUMENT>no xml here") is None
    assert extract_ownership_document("<ownershipDocument>unterminated") is None
