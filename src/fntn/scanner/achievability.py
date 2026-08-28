"""The achievability lens: §0 decisions read back as criteria, and reported.

**What this is, and what it deliberately is not.** The operator wants strategies
that are *achievable*. That word was prose until 27 August 2026, and **every
component of it is implied by a decision already registered**, so it is derived
here rather than chosen.

***This is a LENS and not a fence.*** It **reads** the registered parameter
object and a candidate's declared attributes and **reports**, criterion by
criterion, which are met and which are not, naming the failing one. **It refuses
nothing, it gates nothing, and no funnel step consults it at decision time**, so
it is **procedure** under armed §0.6 and lands without an Annex A.1 row.

**The fence version would be apparatus** and is prepared, not taken: a screen
that *refuses* is a gate, and a gate takes an Annex A.1 row with a predicate. It
is written up in `docs/ACHIEVABILITY.md` and in Annex A.1.

**Every criterion cites the registered decision behind it.** A criterion whose
authority is not written down is a preference wearing a derivation's clothes.

*Two criteria cannot be scored today and say so rather than passing.* A
not-applicable check may never be read as a pass, so ``UNSCORABLE`` is a state
of its own and is never counted as ``MET``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

#: §6.7's participation cap: 2% of median daily notional per session, over at
#: most three sessions, so the largest position a name supports is 6% of ADV.
PARTICIPATION_CAP_PER_SESSION = 0.02
PARTICIPATION_SESSIONS = 3
MAX_PARTICIPATION = PARTICIPATION_CAP_PER_SESSION * PARTICIPATION_SESSIONS

#: The measured US proportional round-trip term, fixed pricing, from §13 row 1's
#: published schedule: 102.01/p basis points of per-share charges plus the SEC
#: fee, which is proportional to VALUE and does not vary with share price.
US_PER_SHARE_BPS_NUMERATOR = 102.01
US_SEC_FEE_BPS = 0.206

#: §4.1's admissible fixed horizons, in sessions.
ADMISSIBLE_HORIZONS = (5, 21, 63)


class Result(str, Enum):
    """Three states, and the third is not a pass.

    ``UNSCORABLE`` means the criterion is real, the candidate is real, and the
    register does not hold the number needed to judge it. Reporting that as a
    pass would be the defect §2 names: a check that could not run recorded as
    one that ran.
    """

    MET = "met"
    FAILED = "failed"
    UNSCORABLE = "unscorable"


@dataclass(frozen=True)
class CriterionResult:
    name: str
    result: Result
    #: The registered decision this criterion derives from. Never blank.
    authority: str
    #: Why, in the candidate's own numbers where there are any.
    detail: str


class LensNotApplicable(RuntimeError):
    """Raised where the lens is pointed at an object that cannot declare.

    **The C1 repair, made structural rather than documentary.** On the run of
    record the lens reported *nine unscorables on every mechanism in both arms*,
    and that was never a reading. Nothing in this package constructs a
    ``Candidate`` from a proposal; the proposal schema has no column for seven
    of the nine criteria; and the system prompt's rule 3 **discards whole** any
    proposal stating an effect size or a horizon, which are the other two. The
    lens can therefore return nothing else on a pointer, at any sample size,
    for ever.

    A refusal beats nine unscorables for the reason the register prefers
    refusals everywhere else: *this mechanism does not say* and *this instrument
    cannot ask* are different claims, and printing the second as the first put a
    category error into a results table where it read as a finding about the
    mechanisms. §13 row 35 was opened off criterion 9 of an instrument that had
    never scored a real object of any kind.
    """


#: The tier a §3.6 pointer carries. The lens was written for §3.5 items, which
#: declare claims; a pointer is a class-level mechanism and declares none.
POINTER_TIER = "pointer"


@dataclass(frozen=True)
class Candidate:
    """What a mechanism declares about itself, at class level.

    Every field is optional because **an absent declaration is not a failure**:
    it is an unscorable criterion, and the two are reported apart.
    """

    mechanism_id: str
    #: `agent` or `random_control`. Carried so the lens can never be read
    #: across arms by accident.
    origin: str = "unrecorded"
    #: ``quantified`` or ``pointer``. **The lens refuses the second outright**
    #: rather than scoring it into nine unscorables: see ``LensNotApplicable``.
    evidence_tier: str = "quantified"
    long_only: Optional[bool] = None
    us_listed: Optional[bool] = None
    min_share_price_usd: Optional[float] = None
    median_daily_notional_usd: Optional[float] = None
    #: Whether the claimed edge survives to the next session's open (§4.3).
    survives_to_next_open: Optional[bool] = None
    claimed_effect_bps: Optional[float] = None
    holding_period_sessions: Optional[int] = None
    #: Whether every input is obtainable without a purchased vendor feed.
    obtainable_without_purchase: Optional[bool] = None
    #: Whether the archive as scoped can price it, survivorship included.
    backtestable: Optional[bool] = None


@dataclass
class LensReading:
    candidate_id: str
    origin: str
    criteria: List[CriterionResult] = field(default_factory=list)

    @property
    def met(self) -> int:
        return sum(1 for c in self.criteria if c.result is Result.MET)

    @property
    def failed(self) -> List[str]:
        return [c.name for c in self.criteria if c.result is Result.FAILED]

    @property
    def unscorable(self) -> List[str]:
        return [c.name for c in self.criteria if c.result is Result.UNSCORABLE]


def minimum_share_price_usd(tolerance_bps: Optional[float]) -> Optional[float]:
    """The price below which no position size reaches the tolerance.

    Derived, not chosen: ``102.01/p + 0.206 <= t``. Returns ``None`` where the
    tolerance is unset, because a floor derived from an unset tolerance is a
    number with nothing behind it.
    """

    if tolerance_bps is None or tolerance_bps <= US_SEC_FEE_BPS:
        return None
    return US_PER_SHARE_BPS_NUMERATOR / (tolerance_bps - US_SEC_FEE_BPS)


def minimum_daily_notional_usd(smallest_position_usd: float) -> float:
    """The ADV a name needs to support the smallest position §6.7 will size.

    ``position / 0.06``, from §6.7's cap of 2% per session over at most three
    sessions. Stated as a function rather than a constant because the position
    depends on a reference-equity currency reading §0 decision 0b did not
    settle, and a constant would hide that.
    """

    return smallest_position_usd / MAX_PARTICIPATION


def score(
    candidate: Candidate,
    tolerance_bps: Optional[float],
    delta_min_floor_bps: Optional[float],
    smallest_position_usd: float,
    account_is_cash: bool = True,
) -> LensReading:
    """Nine criteria, each citing the registered decision behind it.

    Refuses a pointer-tier candidate rather than scoring it: see
    ``LensNotApplicable``. C2 is the other half and is not code -- the lens runs
    where it belongs, on §3.5 items, once the item pipeline produces any. It has
    produced none.
    """

    if candidate.evidence_tier == POINTER_TIER:
        raise LensNotApplicable(
            f"{candidate.mechanism_id} is a pointer-tier mechanism and the lens "
            "reads declarations a pointer cannot carry. Seven criteria read "
            "fields the proposal schema has no column for; criteria 6 and 7 "
            "read an effect size and a horizon, which the clerk is FORBIDDEN "
            "to state and which `agent_overreached_schema` exists to discard. "
            "Scoring it would return nine unscorables on every mechanism at "
            "every sample size, which is a fact about this instrument and not "
            "about the mechanism. Run the lens on a §3.5 item; the item "
            "pipeline has produced none."
        )

    out = LensReading(candidate.mechanism_id, candidate.origin)
    p_min = minimum_share_price_usd(tolerance_bps)
    adv_min = minimum_daily_notional_usd(smallest_position_usd)

    def add(name, value, test, authority, detail_ok, detail_no, detail_none):
        if value is None:
            out.criteria.append(
                CriterionResult(name, Result.UNSCORABLE, authority, detail_none)
            )
            return
        ok = test(value)
        out.criteria.append(
            CriterionResult(
                name, Result.MET if ok else Result.FAILED, authority,
                detail_ok if ok else detail_no,
            )
        )

    add("long_only", candidate.long_only, lambda v: bool(v) and account_is_cash,
        "§14 account type: CASH (P116); §5.4.1 long-only grammar",
        "long-only, and the account is cash",
        "requires a short leg or margin, which a cash account cannot take",
        "the mechanism does not declare a direction")

    add("us_listed", candidate.us_listed, lambda v: bool(v),
        "§0 decision 0b base currency USD; §13 row 29 at 10 bp excludes UK Main "
        "Market on stamp duty and AIM on commission",
        "US-listed", "not US-listed", "the mechanism does not declare a venue")

    add("min_share_price", candidate.min_share_price_usd,
        lambda v: p_min is not None and v >= p_min,
        f"§13 rows 29 and 1: 102.01/p + 0.206 <= tolerance, so p >= "
        f"{p_min:.2f} USD" if p_min else "§13 row 29 is unset",
        f"at or above USD {p_min:.2f}" if p_min else "unscorable",
        f"below USD {p_min:.2f}, where no position size reaches the tolerance"
        if p_min else "unscorable",
        "the mechanism does not declare a minimum share price")

    add("min_liquidity", candidate.median_daily_notional_usd,
        lambda v: v >= adv_min,
        "§6.7 participation cap: 2% of median daily notional per session over "
        f"at most 3 sessions, so ADV >= USD {adv_min:,.0f}",
        f"at or above USD {adv_min:,.0f} of median daily notional",
        f"below USD {adv_min:,.0f}, so §6.7 cannot size even its smallest "
        "position without breaching the cap",
        "the mechanism does not declare a liquidity floor")

    add("actionable_at_next_open", candidate.survives_to_next_open,
        lambda v: bool(v),
        "§4.3 execution convention: entries and signal exits fill at the open "
        "of the session after signal completion; §13 row 13 measures the "
        "capture rate and is BLOCKED",
        "the claimed edge survives to the next open",
        "the edge is consumed intraday before the next open, so this "
        "convention cannot reach it. REFUSED, not discounted",
        "the mechanism does not declare whether its edge survives to the next "
        "open, and §13 row 13 would measure it")

    add("effect_exceeds_delta_min", candidate.claimed_effect_bps,
        lambda v: delta_min_floor_bps is not None and v >= delta_min_floor_bps,
        f"§14 δ_min floor, derived at {delta_min_floor_bps} bp (P117)"
        if delta_min_floor_bps else "§14 δ_min floor is unset",
        f"claimed effect clears {delta_min_floor_bps} bp",
        f"claimed effect is below {delta_min_floor_bps} bp, so it is "
        "unactionable in every cell",
        "the mechanism declares no effect size")

    add("holding_period_admissible", candidate.holding_period_sessions,
        lambda v: v in ADMISSIBLE_HORIZONS,
        "§4.1 fixed horizons {5, 21, 63} sessions. §14's manual-observation "
        "capacity is OPEN and would tighten this, and is not invented here",
        "within the admissible horizons",
        "outside §4.1's admissible horizons",
        "the mechanism declares no holding period")

    add("obtainable_without_purchase", candidate.obtainable_without_purchase,
        lambda v: bool(v),
        "§0.7(d)'s ICB vendor is the only purchase on the register and is not "
        "authorised; no vendor feed is authorised",
        "every input is obtainable without a purchase",
        "needs a purchased vendor feed, so it is not achievable TODAY. It "
        "takes an Annex A.1 row with the purchase as its predicate rather "
        "than being silently dropped",
        "the mechanism does not declare its inputs")

    add("backtestable", candidate.backtestable, lambda v: bool(v),
        "§0.7(a) archive; the survivorship condition of P127; §13 row 35 "
        "holds the coverage fraction and is BLOCKED",
        "priceable against the archive as scoped, survivorship included",
        "not priceable against the archive as scoped",
        "the archive does not exist and §13 row 35's coverage fraction is "
        "unset, so this cannot be scored either way")

    return out
