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

import json
from datetime import date, datetime, timedelta, timezone

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
from fntn.scanner.ledger import Ledger
from fntn.scanner.records import (
    Directive,
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
from fntn.scanner.records import IntakeRecord, ClaimField

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


def run_intake(ctx, subject_id="s1", mode=Mode.FAIL_FAST):
    return intake_runner().run(subject_id, ctx, mode=mode)


# ---------------------------------------------------------------------------
# The structural fence: mechanisms, never episodes.
# ---------------------------------------------------------------------------


#: A stand-in master. In production these are the security master and the
#: discovery markets' listing lists, named in §13 row 22.
MASTER = frozenset({"barclays", "vodafone", "bhp", "aapl", "vod", "acme"})
FENCE = EntityFence(security_master=MASTER, lexicon=SEED_LEXICON)


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
    assert set(codes.INTAKE_ORDER) == {
        rc.code for rc in codes.by_surface(codes.Surface.INTAKE)
    }
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
