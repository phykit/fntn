"""Reason-code registry for the agent discovery scanner.

Spec: From Narrative to Null v1.14 (proposed), §3.7, §8, §9.4.

Every refusal anywhere in this package emits a code defined here and nowhere
else.  §9.4's headline coverage ratio is *codes emitted against codes defined*:
a code defined and never emitted is an untested branch, so the registry is the
denominator of that ratio and is deliberately the only place a code may be
introduced.

Two ingestion surfaces, and the distinction matters:

  * ``INTAKE`` -- turning an agent proposal into a §3.6.2 intake record.  This
    is the surface the fail-fast rule was asked for: the moment a required
    input is absent, the idea is abandoned and the next one starts.
  * ``OBSERVATION`` -- items arriving from a stream a registered directive
    names, running the §3.5 ingestion path.  Same fail-fast discipline, a
    different ordered list, because a pointer has no asset and an item has no
    ``event_class`` intention.

Codes marked ``inherited=True`` already exist in the manuscript and are
restated here so that this package emits the manuscript's code and never a
synonym.  §9.5's linter checks that claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List


class Surface(str, Enum):
    """Which ingestion surface a code belongs to."""

    INTAKE = "intake"
    OBSERVATION = "observation"
    SCREEN = "screen"
    DIRECTIVE = "directive"
    REGISTRATION = "registration"
    SEGMENT = "segment"
    SIZING = "sizing"
    PROVENANCE = "provenance"


@dataclass(frozen=True)
class ReasonCode:
    """One named refusal branch.

    ``summary_template`` is the §8 rejection summary: two to three sentences of
    plain language rendered from the record's own fields by ``str.format``.  It
    is display-only by construction -- nothing in this package reads it back --
    and it is *rendered, never judged*, because a model-written account of a
    deterministic decision would be a probabilistic gloss on an exact fact.

    ``resurrection`` is the machine-checkable predicate under which the idea
    may be re-raised, restated as a sentence in the summary.  A refusal without
    a resurrection predicate is a refusal the ledger cannot ever reverse, and
    §8 does not permit one.
    """

    code: str
    surface: Surface
    description: str
    summary_template: str
    resurrection: str
    inherited: bool = False
    #: True where the refusal is a *refusal to score* (an input is missing or
    #: unverified) rather than a measured failure.  §Σ.3 control surface 1: a
    #: refusal is a state with a reason code, not an absence.
    refuse_to_score: bool = False


# ---------------------------------------------------------------------------
# Surface A -- intake ingestion, in the order the runner applies them.
# ---------------------------------------------------------------------------

_INTAKE: List[ReasonCode] = [
    ReasonCode(
        code="source_inaccessible",
        surface=Surface.INTAKE,
        description=(
            "The document the proposal rests on could not be retrieved at the "
            "cited location."
        ),
        summary_template=(
            "The proposal cited {source_ref}, which could not be retrieved on "
            "{attempted_at} ({detail}). Nothing downstream may read a claim "
            "whose document was never opened, so the idea was abandoned at the "
            "first ingestion point. {resurrection}"
        ),
        resurrection=(
            "Re-raise once the document resolves at a stable location, or once "
            "the operator supplies an archived copy with a retrieval timestamp."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="event_definition_absent",
        surface=Surface.INTAKE,
        description=(
            "The proposal states no mechanism in one sentence, so there is "
            "nothing for §3.6.5's table to classify."
        ),
        summary_template=(
            "The proposal named no event definition, so §3.6.5 had no "
            "mechanism to classify and check 3 had no input to consume. An "
            "idea without a stated mechanism is a topic, not a pointer. "
            "{resurrection}"
        ),
        resurrection=(
            "Re-raise with a one-sentence mechanism in the item-extraction "
            "idiom, naming what happens and to whom."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="measured_on_absent",
        surface=Surface.INTAKE,
        description=(
            "No target population stated, so §3.6.3 check 2 cannot record even "
            "an intention."
        ),
        summary_template=(
            "The proposal stated no target population, so the measured-on "
            "field required by §3.6.3 check 2 was empty. §0.9's error class is "
            "exactly a figure travelling without the set it was measured on, "
            "and the lane will not accept one at intake. {resurrection}"
        ),
        resurrection=(
            "Re-raise naming the market, capitalisation range and filters the "
            "claim is intended to hold on."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="provenance_tag_absent",
        surface=Surface.INTAKE,
        description=(
            "A claim field arrived without a provenance tag, so no consumer can "
            "tell verified fact from recollection."
        ),
        summary_template=(
            "Field {failed_field} carried no provenance tag, so no consumer "
            "could distinguish a verified claim from a recollection. §14 cannot "
            "be signed while an untagged claim feeds anything, and the tag is "
            "cheaper to supply at intake than to reconstruct later. "
            "{resurrection}"
        ),
        resurrection=(
            "Re-raise with verified_primary, verified_secondary or recollection "
            "on every populated claim field."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="intake_budget_exhausted",
        surface=Surface.INTAKE,
        description=(
            "Intake exceeded the registered time ceiling, at one point or "
            "cumulatively over the subject, and the subject is abandoned "
            "rather than held open. Not a verdict on the idea: a verdict on "
            "how long looking at it took."
        ),
        summary_template=(
            "Intake was abandoned at {point} after {elapsed_s}s against a "
            "registered budget of {budget_s}s, on attempt {attempts}. The "
            "ceiling is a ceiling on the cost of looking, not a judgement of "
            "the idea, and the idea is neither refused nor accepted by it. "
            "**This decision was taken once, when the work ran, and the "
            "elapsed time above is the record of it**: a replay reads this "
            "figure and does not re-time the work, so the same inputs produce "
            "the same refusal on any machine. {resurrection}"
        ),
        resurrection=(
            "Re-raise where EITHER the registered budget has been raised above "
            "the elapsed time recorded here, which is a re-stamp with "
            "intake_point_budget_s or intake_subject_budget_s named as the "
            "causing field, OR a later attempt on the same source completed "
            "within the budget in force, which the ledger's own budget rows "
            "show as an unexhausted decision at the same point."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="claim_provenance_recollection",
        surface=Surface.INTAKE,
        description=(
            "A load-bearing claim carries a provenance tag the freeze "
            "signature cannot stand on, so the consuming check refuses to "
            "score. Named for its commonest case, recollection; the set is "
            "Provenance.blocks_freeze_signature and reconstructed_hash_"
            "verified is also in it."
        ),
        summary_template=(
            "Field {failed_field} carried {provenance} provenance, which the "
            "§14 signature cannot stand on, so the consuming check refused to "
            "score rather than guessing. The lane's first intake found a "
            "recollected claim wrong in two places, which is why this refusal "
            "exists and why it is not a nuisance. {resurrection}"
        ),
        resurrection=(
            "Re-raise once the field is verified against the primary document "
            "and re-tagged."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="registered_at_unstampable",
        surface=Surface.INTAKE,
        description=(
            "The proposal's target population already carries a logged "
            "conditional-return query, so the query fence bars registration."
        ),
        summary_template=(
            "The target population {measured_on} was queried for conditional "
            "returns at {fence_breach_at}, before any registration existed for "
            "it. P59 makes a directive whose population was queried that way "
            "pre-registration inadmissible, and the bar is mechanical rather "
            "than a matter of the operator's care. {resurrection}"
        ),
        resurrection=(
            "Not resurrectable on this population within this archive; re-raise "
            "on a population the query log shows clean, or after a partition "
            "boundary the contaminating query does not span."
        ),
    ),
    ReasonCode(
        code="agent_overreached_schema",
        surface=Surface.INTAKE,
        description=(
            "The agent populated a field it holds no authority over -- merit, "
            "evidence tier, abandonment threshold, severity or a stream for an "
            "unclassified class."
        ),
        summary_template=(
            "The proposal populated {failed_field}, which the discovery agent "
            "holds no authority over. The clerk classifies and the table "
            "decides; a proposal that sets its own pass condition has moved "
            "the model from clerk to analyst, and the whole proposal is "
            "discarded rather than trimmed. {resurrection}"
        ),
        resurrection=(
            "Re-raise through the proposal schema with the reserved fields "
            "left empty for the table and the operator to populate."
        ),
    ),
    ReasonCode(
        code="agent_payload_off_schema",
        surface=Surface.INTAKE,
        description=(
            "The model's tool call returned an element the proposal schema "
            "does not describe -- a bare string, a number, a null -- where an "
            "object was required."
        ),
        summary_template=(
            "Element {index} of the returned payload was a {got}, and the "
            "proposal schema requires an object. The element is discarded "
            "whole and not repaired: a forced tool call is not a validated "
            "one, and guessing which field a bare string was meant to be is "
            "the clerk's work being done by the loader. {resurrection}"
        ),
        resurrection=(
            "Re-raise by re-running the sweep; a payload that conforms is "
            "read normally. Structurally resurrectable by enabling strict "
            "schema enforcement on the tool call, which is a registered "
            "decision and not a loader change."
        ),
    ),
    ReasonCode(
        code="agent_payload_not_a_list",
        surface=Surface.INTAKE,
        description=(
            "The model's tool call returned a `proposals` value that is not an "
            "array. The whole call yielded no mechanism, and this is ONE "
            "refusal for the call and not one per element of whatever arrived."
        ),
        summary_template=(
            "The sweep over {corpus_id} returned a `proposals` value of type "
            "{got}, and the schema requires an array. **The whole call yielded "
            "no mechanism** and is counted once. It is counted once because a "
            "string is iterable: reading it element-wise produced {length} "
            "character-shaped refusals on the first live sweep, which inflated "
            "the funnel's denominator by four orders of magnitude and made a "
            "single malformed reply look like a search. {resurrection}"
        ),
        resurrection=(
            "Re-raise by re-running the sweep over the same corpus; the reply "
            "is not deterministic and a conforming one is read normally. "
            "Structurally resurrectable by enabling strict schema enforcement "
            "on the tool call, which is a registered decision (§13) and not a "
            "loader change."
        ),
    ),
    ReasonCode(
        code="security_master_unavailable",
        surface=Surface.INTAKE,
        description=(
            "The entity fence's binding layer is a lookup against the security "
            "master, and no master was supplied."
        ),
        summary_template=(
            "No security master was available to the entity fence, so its "
            "binding layer could not run and only the identifier and "
            "designator patterns were live. The trace that replaced the "
            "pattern-only fence showed patterns alone are not a fence, so the "
            "check refuses to score rather than passing on the weaker half. "
            "{resurrection}"
        ),
        resurrection=(
            "Proceeds as soon as the security master and the discovery markets' "
            "listing lists are loaded and named in the parameter object."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="proposal_names_entity",
        surface=Surface.INTAKE,
        description=(
            "The proposal named an issuer, instrument or dated episode. The "
            "discovery agent emits mechanisms, never episodes."
        ),
        summary_template=(
            "The proposal named {failed_field}, an entity or dated episode "
            "rather than a mechanism. The leak the discovery fence exists to "
            "close runs through the underlying price path, and an episode-level "
            "proposal is precisely the field it would travel in; the whole "
            "proposal is discarded rather than stripped of its names. "
            "{resurrection}"
        ),
        resurrection=(
            "Re-raise the same idea stated as a class-level mechanism, with no "
            "issuer, instrument, ticker or dated episode anywhere in the record."
        ),
    ),
    ReasonCode(
        code="discovery_partition_violation",
        surface=Surface.INTAKE,
        description=(
            "The proposal rests on material drawn from a partition the "
            "discovery agent may not read."
        ),
        summary_template=(
            "The proposal rests on {source_ref}, which sits in the "
            "{failed_field} partition and is not readable by a discovery agent. "
            "Selection and evaluation must share no observations, and the "
            "assertion is made here for the same reason Gate 0 makes it for "
            "manually injected items: an unguarded hole in the separation is a "
            "hole in the instrument being relied on. {resurrection}"
        ),
        resurrection=(
            "Re-raise from readable material, or register the directive under "
            "forward_only scoring so that selection and measurement remain "
            "disjoint in time."
        ),
    ),
    ReasonCode(
        code="scoring_mode_unsatisfiable",
        surface=Surface.INTAKE,
        description=(
            "No exclusivity guarantee can be constructed for this proposal: it "
            "is not cross-market separable, no disjoint partition carries the "
            "class, and forward-only would not reach n_min before the archive "
            "ends."
        ),
        summary_template=(
            "No exclusivity construction is available for "
            "({event_class}, {measured_on}): the class does not occur outside "
            "the traded universe, no disjoint partition carries it, and "
            "forward-only collection would not reach n_min before the archive "
            "ends. A directive with no separation between finding and "
            "evaluation measures the finder. {resurrection}"
        ),
        resurrection=(
            "Admissible once a market outside §0.7(f) carrying the class is "
            "readable, or once the archive extends far enough for forward-only "
            "scoring to reach n_min."
        ),
    ),
    ReasonCode(
        code="duplicate_of_open_pointer",
        surface=Surface.INTAKE,
        description=(
            "The proposal's (event_class, measured_on) pair already has an open "
            "or registered pointer."
        ),
        summary_template=(
            "The pair ({event_class}, {measured_on}) already carries "
            "{duplicate_ref}, raised at {duplicate_registered_at}. A second "
            "directive on the same cell would consume design-segment span "
            "twice for one question and would overlap itself at rho equal to "
            "one. {resurrection}"
        ),
        resurrection=(
            "Re-raise once the incumbent directive reaches a verdict, or as an "
            "amendment to it rather than as a new pointer."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Surface A continued -- screen, directive and registration refusals.
# ---------------------------------------------------------------------------

_SCREEN: List[ReasonCode] = [
    ReasonCode(
        code="no_observable_stream",
        surface=Surface.SCREEN,
        description=(
            "§3.6.3 check 3, binding: no machine-readable, timestamped, "
            "corroborable stream carries the event class."
        ),
        summary_template=(
            "No machine-readable, timestamped and corroborable stream carries "
            "{event_class}, so §3.6.3 check 3 refused the pointer outright. A "
            "directive that names no stream is not a directive, and this is the "
            "one screen a pointer can fail. {resurrection}"
        ),
        resurrection=(
            "Re-raise once a stream carrying the class exists and the operator "
            "can answer the five observability questions about it."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="check_not_applicable_pointer_tier",
        surface=Surface.SCREEN,
        description=(
            "Cost survival and horizon admissibility have no input to consume "
            "on a pointer. Recorded, and never readable as a pass."
        ),
        summary_template=(
            "Checks 1 and 4 reported not-applicable because a pointer states no "
            "claimed effect and no claimed horizon. This is recorded so that a "
            "reader cannot mistake an absent input for a cleared hurdle; a "
            "not-applicable check may never be read as a pass. {resurrection}"
        ),
        resurrection=(
            "Both checks become applicable when the pointer is promoted to a "
            "quantified intake under §3.6.8 step 6."
        ),
        inherited=True,
    ),
]

_DIRECTIVE: List[ReasonCode] = [
    ReasonCode(
        code="stream_requires_new_subscription",
        surface=Surface.DIRECTIVE,
        description=(
            "The named stream needs a production ingestion adapter, which is "
            "apparatus under §0.6."
        ),
        summary_template=(
            "The directive named {stream}, which this system does not ingest "
            "and which would need a parser, anchor semantics and a "
            "parameter-object footprint to obtain. That is apparatus however "
            "modestly it is described, so the row waits behind its Annex A.1 "
            "predicate and the feed is logged against the roster decision. "
            "{resurrection}"
        ),
        resurrection=(
            "Admissible once the §0.6 instruments have reported and this "
            "directive has a pre-registered measurement it cannot run on any "
            "existing stream."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="stream_unmapped_pending_operator",
        surface=Surface.DIRECTIVE,
        description=(
            "The event class classified as unclassified. The agent proposes no "
            "stream; the operator names one by hand."
        ),
        summary_template=(
            "The class {event_class} sits outside §3.6.5's table, so the agent "
            "emitted unclassified and proposed no stream, having no authority "
            "to invent one. The mapping waits on the operator answering the "
            "five observability questions by hand. {resurrection}"
        ),
        resurrection=(
            "Proceeds as soon as the operator records publisher, access route, "
            "machine-readability, per-item timestamps and corroborability."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="manual_observation_capacity_exhausted",
        surface=Surface.DIRECTIVE,
        description=(
            "The stream is collectable by hand but the operator's registered "
            "manual-observation capacity for the period is already committed."
        ),
        summary_template=(
            "{stream} is collectable under the manual-observation protocol, but "
            "the period's registered capacity of {capacity} slots is already "
            "committed. Collection when something interesting happens is not "
            "collection, so the cadence is not stretched to fit an extra "
            "directive. {resurrection}"
        ),
        resurrection=(
            "Admissible at the next period boundary, or immediately if the "
            "operator retires an open manual protocol and records the swap."
        ),
    ),
]

_REGISTRATION: List[ReasonCode] = [
    ReasonCode(
        code="confound_unmeasurable",
        surface=Surface.REGISTRATION,
        description=(
            "P58 pre-mortem: the most plausible false-mechanism explanation "
            "cannot be measured on available data."
        ),
        summary_template=(
            "The pre-mortem named {confound} as the most plausible reason the "
            "observation would show an effect even if the mechanism is false, "
            "and that confound is not measurable on available data. The pointer "
            "is refused here rather than after it has consumed a session of "
            "the design segment. {resurrection}"
        ),
        resurrection=(
            "Re-raise once data measuring the named confound is in the stack, "
            "or with a design that separates the confound from the mechanism."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="premortem_unratified",
        surface=Surface.REGISTRATION,
        description=(
            "The pre-mortem was drafted by the agent and has not been ratified "
            "by the operator."
        ),
        summary_template=(
            "The pre-mortem for this directive was drafted by the discovery "
            "agent and carries author=agent, ratified=false. §8 requires the "
            "decision's own author where the decision is human, and a "
            "machine-drafted falsification condition the operator has not read "
            "is not a commitment. {resurrection}"
        ),
        resurrection=(
            "Registration proceeds the moment the operator ratifies or rewrites "
            "the pre-mortem and the ledger records the author."
        ),
    ),
    ReasonCode(
        code="delta_min_absent",
        surface=Surface.REGISTRATION,
        description=(
            "No abandonment threshold. The agent may not supply one and the "
            "operator has not."
        ),
        summary_template=(
            "No abandonment threshold was registered for this directive. "
            "delta_min is the magnitude the operator commits to before knowing "
            "whether it flatters them, and a threshold supplied by the same "
            "process that raised the idea would return the pass condition to "
            "the party that wants it to pass. {resurrection}"
        ),
        resurrection=(
            "Registration proceeds once the operator states delta_min in the "
            "units the measurement reports, at or above the §14 floor."
        ),
    ),
    ReasonCode(
        code="registered_sign_absent",
        surface=Surface.REGISTRATION,
        description=(
            "No registered sign, or one outside {-1, +1}. The agent may not "
            "supply it and the operator has not."
        ),
        summary_template=(
            "No direction was registered for this directive. §3.6.8 step 4 "
            "makes the sign one of four parts that must exist before any "
            "observation, and it was the only one nothing refused on: a "
            "directive could register without it and have its direction chosen "
            "once the answer was known, which is the endogeneity the "
            "equivalence verdicts were adopted to close. {resurrection}"
        ),
        resurrection=(
            "Registration proceeds once the operator states the sign as -1 or "
            "+1, before any data on the target population is examined."
        ),
    ),
    ReasonCode(
        code="delta_min_below_floor",
        surface=Surface.REGISTRATION,
        description=(
            "The registered abandonment threshold is below the §14 floor, so"
            "the directive is not worth a session of the segment."
        ),
        summary_template=(
            "delta_min was registered at {delta_min} against a floor of "
            "{delta_min_floor}. An effect smaller than the floor would not "
            "change a deployment decision even if it were real, so the segment "
            "span it would consume buys nothing. {resurrection}"
        ),
        resurrection=(
            "Re-raise at or above the floor, or bring a §0 decision to move the "
            "floor with its arithmetic on the record."
        ),
    ),
    ReasonCode(
        code="literature_search_absent",
        surface=Surface.REGISTRATION,
        description="P60: no literature search was run and recorded.",
        summary_template=(
            "No literature search was recorded before registration. Either the "
            "idea is already published, in which case it enters as a paper "
            "intake with a decay prior and someone else's referees, or it is "
            "not, and why not is itself an answer the published literature "
            "systematically declines to supply. {resurrection}"
        ),
        resurrection=(
            "Registration proceeds once the search is run and its result -- "
            "including a null result and its interpretation -- is recorded."
        ),
        inherited=True,
    ),
]

_SEGMENT: List[ReasonCode] = [
    ReasonCode(
        code="segment_overlap_exceeds_theta",
        surface=Surface.SEGMENT,
        description=(
            "Admitting the directive would push a pairwise design-segment "
            "overlap above the registered tolerance θ."
        ),
        summary_template=(
            "Admitting this directive would raise pairwise overlap with "
            "{worst_pair} to {overlap:.2f} against a tolerance of {theta:.2f}. "
            "An over-reused design segment quietly stops being out of sample "
            "for anything measured on it, and the arithmetic refuses rather "
            "than the operator judging. {resurrection}"
        ),
        resurrection=(
            "Admissible when the overlapping directive closes, or on a "
            "re-registered span that keeps every pairwise overlap within θ."
        ),
    ),
    ReasonCode(
        code="segment_reserved_for_calibration",
        surface=Surface.SEGMENT,
        description=(
            "The segment's unconsumed span is at or below the floor the pending "
            "§13 calibrations require, which hold first claim."
        ),
        summary_template=(
            "The design segment's unconsumed span is {available} sessions "
            "against a calibration reserve of {reserve}. The §13 calibrations "
            "have first claim on the segment and directives take the residual, "
            "so this draft queues rather than displacing a calibration. "
            "{resurrection}"
        ),
        resurrection=(
            "Admissible once the pending calibrations release their reserve, or "
            "once the archive span extends."
        ),
    ),
    ReasonCode(
        code="queued_behind_capacity",
        surface=Surface.SEGMENT,
        description=(
            "Registration-ready, but the segment arithmetic admits by smallest "
            "span first and this draft is not yet at the head of the queue."
        ),
        summary_template=(
            "The draft is registration-ready and queued at position "
            "{queue_position} of {queue_length}, ordered by smallest registered "
            "segment span and then by registration time. Agent-origin drafts "
            "queue rather than displace, so the machine cannot evict the "
            "operator's own directives by out-producing them. {resurrection}"
        ),
        resurrection=(
            "Admitted automatically when the queue reaches it and the segment "
            "arithmetic clears."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Surface B -- observation ingestion, in the order the runner applies them.
# ---------------------------------------------------------------------------

_OBSERVATION: List[ReasonCode] = [
    ReasonCode(
        code="item_source_inaccessible",
        surface=Surface.OBSERVATION,
        description="The item's document could not be retrieved.",
        summary_template=(
            "Item {item_id} cited {source_ref}, which could not be retrieved "
            "({detail}). The item was abandoned at the first ingestion point "
            "and the next item started; the gap is recorded as a gap, never as "
            "an absence of events. {resurrection}"
        ),
        resurrection="Re-ingest when the document resolves.",
        refuse_to_score=True,
    ),
    ReasonCode(
        code="running_document_no_anchor",
        surface=Surface.OBSERVATION,
        description=(
            "document_type is running, so the item carries no publication "
            "moment and may take no anchor role."
        ),
        summary_template=(
            "Item {item_id} is a running document, whose stable topic and "
            "unstable content make t_pub_earliest a republication timestamp "
            "rather than a publication moment. It may seed upstream tracing and "
            "takes no anchor role, so it cannot carry an observation. "
            "{resurrection}"
        ),
        resurrection=(
            "Not resurrectable as an anchored item; a static item covering the "
            "same event may be ingested in its place."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="anchor_provenance_absent",
        surface=Surface.OBSERVATION,
        description=(
            "An anchor arrived without provenance, so its safe-error direction "
            "is unknown."
        ),
        summary_template=(
            "Anchor {failed_field} on item {item_id} arrived without "
            "provenance, so it is not known whether the value is a visible "
            "date, a feed timestamp, content-management metadata or an "
            "inference. Content-management metadata routinely predates "
            "publication, which would run Gate 2's window over a period before "
            "the catalyst existed. {resurrection}"
        ),
        resurrection="Re-ingest once the anchor's provenance is recorded.",
        refuse_to_score=True,
    ),
    ReasonCode(
        code="observation_anchor_absent",
        surface=Surface.OBSERVATION,
        description=(
            "t_pub_observed is absent, so there is no moment at which this "
            "system could have acted."
        ),
        summary_template=(
            "Item {item_id} carries no t_pub_observed, so there is no moment at "
            "which this system could have acted on it and no anchor for the "
            "forward ledger. Every consumer that would read it names it "
            "explicitly, and none has a fallback. {resurrection}"
        ),
        resurrection="Re-ingest with the observation timestamp recorded.",
        refuse_to_score=True,
    ),
    ReasonCode(
        code="ingestion_lag_exceeds_window",
        surface=Surface.OBSERVATION,
        description=(
            "Ingestion lag exceeds the stated fraction of the tuple's "
            "admissible horizon."
        ),
        summary_template=(
            "Item {item_id} reached this system {lag} sessions after "
            "publication, against a ceiling of {lag_ceiling} for a horizon of "
            "{horizon}. The entry window had closed before the item arrived, "
            "which is the quantity §0.9's breadth case depends on and which "
            "nothing measured before this rule existed. {resurrection}"
        ),
        resurrection=(
            "Admissible at a longer admissible horizon, or once the source's "
            "realised lag distribution improves."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="extraction_class_suspended",
        surface=Surface.OBSERVATION,
        description=(
            "The extraction class is below its per-field accuracy floor and is "
            "suspended."
        ),
        summary_template=(
            "Extraction class {extraction_class} is suspended, having fallen "
            "below its accuracy floor at the last quarterly re-draw. "
            "Suspensions lift on the calendar and on a freshly drawn set, never "
            "on demand and never gated on throughput, so the item is abandoned "
            "rather than extracted at a known-degraded accuracy. "
            "{resurrection}"
        ),
        resurrection=(
            "Admissible at the next quarterly review if the class clears its "
            "floor on a freshly drawn set."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="extraction_schema_incomplete",
        surface=Surface.OBSERVATION,
        description=(
            "The schema-enforced extraction call did not return every mandatory "
            "field."
        ),
        summary_template=(
            "Extraction of item {item_id} returned no value for "
            "{failed_field}, which the schema marks mandatory. The clerk's "
            "output is an input to arithmetic and never an authority over it, "
            "so an absent field is a refusal rather than a default. "
            "{resurrection}"
        ),
        resurrection=(
            "Re-ingest on a content hash change, or after a schema revision "
            "that makes the field optional with its consumers restated."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="issuer_unresolved",
        surface=Surface.OBSERVATION,
        description=(
            "The issuer could not be resolved to a primary listing."
        ),
        summary_template=(
            "The issuer referenced by item {item_id} did not resolve to a "
            "primary listing ({detail}). Resolution is unconditional and Gate "
            "1's universe test is a separate rule, so an unresolvable issuer "
            "dies here rather than reaching a gate that would report a "
            "different reason. {resurrection}"
        ),
        resurrection=(
            "Re-ingest once the identifier maps, or once the security master "
            "covers the listing."
        ),
    ),
    ReasonCode(
        code="catalyst_date_corroborated",
        surface=Surface.OBSERVATION,
        description=(
            "The claimed catalyst date is not corroborated against a subscribed "
            "calendar or a regulator-stamped filing."
        ),
        summary_template=(
            "The catalyst date claimed by item {item_id} is not corroborated "
            "against a machine-readable calendar or a regulator-stamped filing, "
            "so the claimed-date cell is inadmissible. Filings are "
            "self-corroborating because the filing is the event; a claim in "
            "prose is not. {resurrection}"
        ),
        resurrection=(
            "Admissible if the event later appears on a subscribed calendar "
            "with a per-item timestamp."
        ),
        inherited=True,
    ),
    ReasonCode(
        code="catalyst_duration_below_floor",
        surface=Surface.OBSERVATION,
        description=(
            "The catalyst resolves inside a single session, so it is "
            "inadmissible to every fixed-horizon family."
        ),
        summary_template=(
            "The catalyst on item {item_id} resolves inside a single session. "
            "Speed buys nothing for a daily-bar instrument, and the exclusion "
            "that already applies to information diffusing sub-session applies "
            "identically to the event itself. {resurrection}"
        ),
        resurrection=(
            "Admissible only under an intraday data dependency, which is an "
            "Annex A.1 row."
        ),
    ),
    ReasonCode(
        code="observation_precedes_registration",
        surface=Surface.OBSERVATION,
        description=(
            "The item is dated before the directive's registered_at, so it is "
            "inadmissible to that directive."
        ),
        summary_template=(
            "Item {item_id} is dated {item_date}, before the directive was "
            "registered at {registered_at}. Observations predating registration "
            "are inadmissible: the rule does not stop hindsight, it stops "
            "hindsight being added after the fact and makes the ordering "
            "auditable. {resurrection}"
        ),
        resurrection=(
            "Not resurrectable for this directive; the item remains available "
            "to any directive registered before it."
        ),
        inherited=True,
    ),
]


# ---------------------------------------------------------------------------
# Surface G -- sizing.  The derived clip floor (§13 rows 29 and 30).
#
# The clip was a chosen constant and is now DERIVED from a governance tolerance
# (row 29) and the measured fixed round-trip cost (row 1).  Two of these three
# codes fire because an input is absent, and the third because **no size
# satisfies the tolerance at all**, which is a measured fact about a market and
# not a missing input.  Keeping them apart is the whole point: an unreachable
# market and an unset parameter look identical from outside and mean opposite
# things.
# ---------------------------------------------------------------------------

_SIZING: List[ReasonCode] = [
    ReasonCode(
        code="clip_floor_tolerance_unset",
        surface=Surface.SIZING,
        description=(
            "§13 row 29's maximum tolerable fixed cost is not set, so the clip "
            "floor has no target to derive against."
        ),
        summary_template=(
            "The clip floor for {market} could not be derived because §13 row "
            "29, the maximum tolerable fixed cost in basis points of position, "
            "is not set. Position size is therefore UNDETERMINED and no "
            "position is taken. This is a refusal to score and not a size of "
            "zero: a zero would say the position was evaluated and came out "
            "small. {resurrection}"
        ),
        resurrection=(
            "Resurrectable the moment §13 row 29 is set by operator governance."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="clip_floor_cost_unset",
        surface=Surface.SIZING,
        description=(
            "§13 row 1's fixed round-trip cost is not established for this "
            "market, so there is nothing to compare against the tolerance."
        ),
        summary_template=(
            "The clip floor for {market} could not be derived because §13 row "
            "1's fixed round-trip cost is not established for it: {missing} is "
            "unset. Row 1 runs first precisely because every break-even "
            "denominator inherits it. Position size is UNDETERMINED and no "
            "position is taken. {resurrection}"
        ),
        resurrection=(
            "Resurrectable when §13 row 1 closes for this market against a "
            "cited, published schedule."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="clip_floor_unreachable_at_any_size",
        surface=Surface.SIZING,
        description=(
            "The size-independent share of the round-trip cost already equals "
            "or exceeds the tolerance, so no position size satisfies it."
        ),
        summary_template=(
            "No position size in {market} satisfies §13 row 29's tolerance of "
            "{tolerance_bps} bp. The size-INDEPENDENT share of the round trip "
            "is {proportional_bps} bp, which does not fall as the position "
            "grows, so the tolerance is exceeded at every size and there is no "
            "floor to derive. This is a measured fact about the market's cost "
            "structure, not a missing input. {resurrection}"
        ),
        resurrection=(
            "Resurrectable if §13 row 29's tolerance is raised above the "
            "size-independent share, or if a cost tier removes part of that "
            "share for a subset of names (Annex A.1)."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Registry.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Surface H -- provenance.  Can this be produced again?
#
# Three times this project depended on material that turned out not to be
# retrievable: the raw fetched pages were never retained, the object behind the
# registration chain's first hash survives only as a reconstruction, and the
# corpus the twelve queued drafts were swept from is in no commit at all.
# **Each was closed as an instance and the class stayed open**, which is how it
# recurred twice more.  These two codes address the class from both ends: one
# refuses to CREATE a record that cannot be reproduced, and one MARKS a record
# that already cannot be.
# ---------------------------------------------------------------------------

_PROVENANCE: List[ReasonCode] = [
    ReasonCode(
        code="corpus_not_committed",
        surface=Surface.PROVENANCE,
        description=(
            "A registered corpus route holds content that no commit carries, "
            "so a sweep over it could not be reproduced from its parameter "
            "hash."
        ),
        summary_template=(
            "The sweep did not run. Corpus route {route} {detail}, so a "
            "proposal raised from it could not be replayed from the parameter "
            "hash it would carry. Rule 1 requires every decision to be "
            "replayable byte-for-byte from that hash, and a corpus git cannot "
            "produce again makes that false at the first step. Nothing was "
            "read and nothing was written. {resurrection}"
        ),
        resurrection=(
            "Resurrectable the moment the corpus is committed: commit it and "
            "re-run the sweep, which then carries a hash a reader can go back "
            "to."
        ),
        refuse_to_score=True,
    ),
    ReasonCode(
        code="population_not_replayable",
        surface=Surface.PROVENANCE,
        description=(
            "A ledger record whose deciding material is not retrievable. "
            "Marked, never deleted: rule 4 says nothing is removed, and a "
            "record that cannot be reproduced is still a record of what "
            "happened."
        ),
        summary_template=(
            "{subject_id} is marked NOT REPLAYABLE. It was raised under "
            "parameter hash {parameter_hash} over {material}, so the sweep "
            "that produced it cannot be reproduced byte-for-byte. The record "
            "is retained in full and "
            "nothing about its content is withdrawn: what is withdrawn is the "
            "claim that it could be replayed. {resurrection}"
        ),
        resurrection=(
            "Not resurrectable by retention: keeping the material now would "
            "not make this record reproducible. Only a fresh sweep under a "
            "registration that names a committed corpus produces a replayable "
            "population."
        ),
        refuse_to_score=False,
    ),
]


ALL_CODES: Dict[str, ReasonCode] = {
    rc.code: rc
    for rc in (*_INTAKE, *_SCREEN, *_DIRECTIVE, *_REGISTRATION, *_SEGMENT, *_SIZING, *_PROVENANCE, *_OBSERVATION)
}

#: The ordered fail-fast sequence for each surface.  Stated explicitly rather
#: than derived from definition order, because the ordering is part of the
#: parameter object and must not change when a file is tidied: a different
#: order produces a different reason-code distribution over the same corpus,
#: and §7.2's attribution would read the difference as a change in the world.
#:
#: Intake is ordered on §2's rule -- kill rate per unit of compute -- subject to
#: one override: the three fences run before anything opens a document.  A
#: proposal that breaches a fence must not have its source retrieved, its
#: duplicates searched or its exclusivity construction computed, because a
#: cheap refusal that has already read the thing it refuses is not cheap.
INTAKE_ORDER: List[str] = [
    # Fences: free, and they must precede reading.
    "agent_overreached_schema",
    # `agent_payload_off_schema` is deliberately NOT here. Intake positions are
    # what §13 row 23's abort-position distribution is measured over, so
    # inserting a code shifts every position after it and makes an earlier
    # reading incomparable with a later one. The code is also emitted before a
    # subject exists: the element never became a proposal, so it never entered
    # intake and has no abort position to report.
    "security_master_unavailable",
    "proposal_names_entity",
    "discovery_partition_violation",
    # Schema completeness: free.
    "event_definition_absent",
    "measured_on_absent",
    # Ledger lookups: cheap, and they bar work that would otherwise be wasted.
    "duplicate_of_open_pointer",
    "registered_at_unstampable",
    "scoring_mode_unsatisfiable",
    # Retrieval: the first costly point on this surface.
    "source_inaccessible",
    # Content-dependent: require the retrieved document.
    "provenance_tag_absent",
    "claim_provenance_recollection",
]

#: Observation is ordered as the §3.5 path already runs, cheapest anchor checks
#: before the schema-enforced extraction call, which is the expensive step.
OBSERVATION_ORDER: List[str] = [rc.code for rc in _OBSERVATION]

#: Intake codes that are NOT positions in the panel, named exhaustively.
#:
#: The ordering invariant below exists so that a code cannot be defined without
#: a place in the sequence, which would leave a refusal nothing could locate.
#: ``intake_budget_exhausted`` is the one refusal that genuinely has no place in
#: it: a ceiling on time is not a check that runs after the twelfth, it is an
#: interruption that can fall at any of them, and giving it position 13 would
#: say every budget abandonment happened after every other check passed. §13 row
#: 23 counts abort positions, so that lie would land directly in a calibration.
#: The set is named rather than the invariant relaxed, so adding a second
#: non-positional code is a deliberate act with this comment in front of it.
#:
#: ``agent_payload_off_schema`` is the second, added 27 August 2026 and for a
#: different reason from the first. It is not an interruption; it is emitted
#: **before a subject exists**. An element of the returned payload that is not
#: an object never becomes a `Proposal`, so it never enters intake and there is
#: no position at which it could have aborted. Giving it position 1 would put a
#: parse failure into §13 row 23's distribution as though the first check had
#: refused it, and shifting the twelve to make room would make every abort
#: position recorded before today incomparable with every one recorded after.
INTAKE_NON_POSITIONAL: frozenset = frozenset({
    "intake_budget_exhausted",
    "agent_payload_off_schema",
    "agent_payload_not_a_list",
})

_declared = set(INTAKE_ORDER) | INTAKE_NON_POSITIONAL
_defined = {rc.code for rc in _INTAKE}
if _declared != _defined:
    raise RuntimeError(
        "INTAKE_ORDER and the intake code definitions disagree: "
        f"ordered-not-defined={sorted(_declared - _defined)}, "
        f"defined-not-ordered={sorted(_defined - _declared)}"
    )
if INTAKE_NON_POSITIONAL & set(INTAKE_ORDER):
    raise RuntimeError(
        "a code cannot be both a position and non-positional: "
        + ", ".join(sorted(INTAKE_NON_POSITIONAL & set(INTAKE_ORDER)))
    )
del _declared, _defined


def by_surface(surface: Surface) -> List[ReasonCode]:
    return [rc for rc in ALL_CODES.values() if rc.surface is surface]


def coverage(emitted: Iterable[str]) -> "CoverageReport":
    """§9.4's headline ratio, computed over this package's own codes."""

    emitted_set = {c for c in emitted}
    unknown = sorted(emitted_set - set(ALL_CODES))
    if unknown:
        raise ValueError(
            "emitted codes not present in the registry: "
            + ", ".join(unknown)
            + " -- a code emitted from outside the registry cannot be counted, "
            "and a kill that cannot be counted cannot be shown to have been "
            "reached"
        )
    never = sorted(set(ALL_CODES) - emitted_set)
    return CoverageReport(
        defined=len(ALL_CODES),
        emitted=len(emitted_set),
        never_emitted=never,
    )


@dataclass(frozen=True)
class CoverageReport:
    defined: int
    emitted: int
    never_emitted: List[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.emitted / self.defined if self.defined else 0.0

    def render(self) -> str:
        lines = [
            "Reason-code coverage (§9.4)",
            f"  defined: {self.defined}",
            f"  emitted: {self.emitted}  ({self.ratio:.0%})",
        ]
        if self.never_emitted:
            lines.append("  defined but never emitted -- untested branches:")
            lines.extend(f"    {c}" for c in self.never_emitted)
        else:
            lines.append("  every defined code has been emitted at least once")
        return "\n".join(lines)
