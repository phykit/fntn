"""The derived clip floor: §13 rows 29 and 30.

**What changed, and why this module exists at all.** The clip was a chosen
constant. §0.11 of 27 August 2026 withdrew the chosen number and replaced it
with a **derivation**: the floor is the smallest position at which §13 row 1's
fixed round-trip cost falls at or below §13 row 29's tolerance. **One free
parameter survives, row 29's tolerance, and the derivation cannot eliminate
it**; everything else follows from a measurement.

**The cost, stated plainly, because it is the reason this module refuses more
than it computes.** Row 29 is OPEN and row 1 is PROVISIONAL, so **the floor
does not currently derive for any market**. Position size is therefore
UNDETERMINED and the book takes no positions.

**That refusal is the point and is not a workaround.** A chosen floor of
£50,000 would have produced the same empty book, and §0.6 names why that would
be worse: *a funnel calibrated to reject everything returns a null
indistinguishable from "there is nothing here"*. A refusal carrying
`clip_floor_tolerance_unset` says which parameter is missing and what would
resurrect it. An empty book under a chosen constant says nothing at all.

**Two shapes of cost, and separating them is what makes the UK result fall
out.** A round trip carries an **absolute** part in the market's currency,
which decays as a share of the position as the position grows, and a
**proportional** part in basis points, which does not decay at any size. Where
the proportional part alone already meets or exceeds the tolerance,
`clip_floor_unreachable_at_any_size` fires: **there is no floor, because no
size works.** That is a measured fact about a market's cost structure and never
a missing input, which is why it carries its own code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from . import summaries
from .records import Refusal

#: Basis points per unit. Named so the arithmetic below reads as arithmetic.
BPS = 10_000.0


@dataclass(frozen=True)
class FixedCost:
    """§13 row 1's round-trip cost for one market, split by how it scales.

    ``absolute_round_trip`` is every per-order and per-conversion charge that
    does **not** scale with the position, summed over the whole round trip, in
    ``currency``. ``proportional_bps`` is every charge that scales with it,
    in basis points of position, summed over the whole round trip.

    **Both are ``None`` until §13 row 1 closes for this market**, and ``None``
    is refused rather than defaulted: a zero here would assert a measurement
    that no schedule has supplied.
    """

    market: str
    currency: str
    absolute_round_trip: Optional[float] = None
    proportional_bps: Optional[float] = None
    #: §0.5's vocabulary. Recorded so a derived floor carries the provenance of
    #: the cost it was derived from and never a better one.
    provenance: str = "unset"


@dataclass(frozen=True)
class ClipFloor:
    """A derived floor, with the inputs it was derived from.

    Carries its inputs because a floor is only as good as the row 1 reading
    behind it, and a number that has lost its provenance is a number that will
    be quoted under a hash it was never taken under.
    """

    market: str
    currency: str
    floor: float
    tolerance_bps: float
    cost: FixedCost

    @property
    def provenance(self) -> str:
        return self.cost.provenance


def derive_clip_floor(
    cost: FixedCost,
    tolerance_bps: Optional[float],
    subject_id: str = "clip-floor",
) -> Union[ClipFloor, Refusal]:
    """The smallest position whose fixed round trip costs at most the tolerance.

    **The derivation, as a function and not a number:**

    ``floor = absolute_round_trip / ((tolerance_bps - proportional_bps) / 10000)``

    The proportional part is subtracted from the tolerance first because it is
    paid at every size; what is left is the budget the absolute part must fit
    inside, and dividing gives the size at which it just does.

    **Refuses rather than defaults, in three named ways**, and the third is not
    a failure of inputs:

    * ``clip_floor_tolerance_unset`` -- row 29 is not set.
    * ``clip_floor_cost_unset`` -- row 1 is not established for this market.
    * ``clip_floor_unreachable_at_any_size`` -- the proportional share alone
      meets or exceeds the tolerance, so **no size satisfies it**. There is no
      floor to return and returning a very large number instead would say the
      market was reachable at a price.
    """

    if tolerance_bps is None:
        return summaries.render(
            "clip_floor_tolerance_unset", subject_id, {"market": cost.market}
        )
    missing = [
        name for name, value in (
            ("absolute_round_trip", cost.absolute_round_trip),
            ("proportional_bps", cost.proportional_bps),
        ) if value is None
    ]
    if missing:
        return summaries.render(
            "clip_floor_cost_unset",
            subject_id,
            {"market": cost.market, "missing": " and ".join(missing)},
        )
    if cost.proportional_bps >= tolerance_bps:
        return summaries.render(
            "clip_floor_unreachable_at_any_size",
            subject_id,
            {
                "market": cost.market,
                "tolerance_bps": f"{tolerance_bps:g}",
                "proportional_bps": f"{cost.proportional_bps:g}",
            },
        )
    budget_bps = tolerance_bps - cost.proportional_bps
    return ClipFloor(
        market=cost.market,
        currency=cost.currency,
        floor=cost.absolute_round_trip / (budget_bps / BPS),
        tolerance_bps=tolerance_bps,
        cost=cost,
    )


def cost_at(cost: FixedCost, position: float) -> Optional[float]:
    """The round-trip cost of a position, in basis points, or None if unset.

    The inverse reading of the derivation, kept beside it so a table of floors
    and a table of costs cannot drift apart.
    """

    if cost.absolute_round_trip is None or cost.proportional_bps is None:
        return None
    if position <= 0:
        return None
    return cost.proportional_bps + BPS * cost.absolute_round_trip / position


# ---------------------------------------------------------------------------
# The US per-share schedule, and why the "residual" was never a residual.
# ---------------------------------------------------------------------------
#
# §13 row 1 records ~19 bp at about USD 3,200 and ~3 bp at USD 64,000. Fitting
# a single (absolute, proportional) pair to those two points gave absolute
# ~USD 5.39 and proportional ~2.16 bp, and the proportional part looked like a
# term nobody could name.
#
# **It is the per-share commission, and the reason it looked mysterious is a
# REGIME CHANGE rather than a missing term.** A per-share commission is
# proportional to trade value at a fixed share price, so it never decays; but
# it carries a per-order minimum, and below the size where the rate overtakes
# that minimum it behaves as a fixed cost and decays like one. The small
# reading sits in the minimum regime and the large one in the rate regime, and
# a single linear model cannot straddle the boundary.
#
# **The consequence is the valuable part: the US hard floor is not a constant.
# It is a function of share price**, and a tight tolerance therefore excludes
# low-priced US stocks at any position size, in the same way and for the same
# reason that stamp duty excludes UK Main Market at any position size. That is
# the project's first screening rule DERIVED from the cost table rather than
# chosen.


@dataclass(frozen=True)
class PerShareSchedule:
    """A US commission schedule expressed per share, with its order minimum.

    ``clearing_per_share`` is the NSCC/DTC charge, applied on both sides.
    Per-share regulatory terms that this does not name (FINRA's trading
    activity fee on the sell leg, the SEC fee on sell value) are **left out
    rather than guessed**: neither rate was read from a published schedule in
    this tree. They are small and they push every figure below in the same
    direction, so **every minimum share price here is a LOWER bound.**
    """

    name: str
    per_share: float
    order_minimum: float = 1.00
    clearing_per_share: float = 0.0002


#: The two elections §13 row 1's tiered-or-fixed gap is between.
US_FIXED = PerShareSchedule("US fixed", 0.005)
US_TIERED = PerShareSchedule("US tiered", 0.0035)

#: Manual spot conversion, both legs: USD 2.00 minimum against 0.20 bp.
FX_ABSOLUTE_ROUND_TRIP = 4.00


def hard_floor_bps(schedule: PerShareSchedule, share_price: float) -> float:
    """The basis-point cost NO position size can get below, at this price.

    ``(2 * per_share + 2 * clearing) / share_price``, in basis points. Both
    terms are per share, so both are proportional to trade value at a fixed
    price and **neither decays as the position grows.**
    """

    per_share_total = 2 * (schedule.per_share + schedule.clearing_per_share)
    return BPS * per_share_total / share_price


def minimum_share_price(schedule: PerShareSchedule, tolerance_bps: float) -> float:
    """The lowest share price at which the tolerance is achievable at all.

    Inverts ``hard_floor_bps``. **Below this price no position size in this
    name satisfies the tolerance**, which is a screening rule on the universe
    and not a sizing rule.
    """

    per_share_total = 2 * (schedule.per_share + schedule.clearing_per_share)
    return BPS * per_share_total / tolerance_bps


def us_round_trip_bps(
    schedule: PerShareSchedule,
    trade_value: float,
    share_price: float,
    fx_absolute: float = FX_ABSOLUTE_ROUND_TRIP,
) -> float:
    """Round-trip fixed cost in basis points, across BOTH regimes.

    Below ``order_minimum * share_price / per_share`` the minimum binds and the
    cost decays like a fixed charge; above it the rate binds and the cost is
    flat in size. **A model that straddles that boundary linearly is the model
    that produced the unexplained residual.**
    """

    shares = trade_value / share_price
    commission = 2 * max(schedule.order_minimum, schedule.per_share * shares)
    clearing = 2 * schedule.clearing_per_share * shares
    return BPS * (commission + clearing + fx_absolute) / trade_value


def rate_regime_from(schedule: PerShareSchedule, share_price: float) -> float:
    """The trade value at which the per-share rate overtakes the minimum."""

    return schedule.order_minimum * share_price / schedule.per_share


def us_clip_floor(
    schedule: PerShareSchedule,
    share_price: float,
    tolerance_bps: Optional[float],
    subject_id: str = "clip-floor-us",
) -> Union[ClipFloor, Refusal]:
    """The US floor at a given share price, or the refusal that no size works.

    **`clip_floor_unreachable_at_any_size` fires wherever the tolerance sits at
    or below the hard floor for that price**, which is the requirement that its
    distinction from a refusal to score survives: an unreachable name and an
    unset parameter look identical from outside and mean opposite things.
    """

    if tolerance_bps is None:
        return summaries.render(
            "clip_floor_tolerance_unset", subject_id, {"market": schedule.name}
        )
    hard = hard_floor_bps(schedule, share_price)
    if hard >= tolerance_bps:
        return summaries.render(
            "clip_floor_unreachable_at_any_size",
            subject_id,
            {
                "market": f"{schedule.name} at USD {share_price:g} per share",
                "tolerance_bps": f"{tolerance_bps:g}",
                "proportional_bps": f"{hard:.2f}",
            },
        )
    lo, hi = 1.0, 1e9
    for _ in range(200):
        mid = (lo + hi) / 2
        if us_round_trip_bps(schedule, mid, share_price) > tolerance_bps:
            lo = mid
        else:
            hi = mid
    return ClipFloor(
        market=f"{schedule.name} at USD {share_price:g} per share",
        currency="USD",
        floor=hi,
        tolerance_bps=tolerance_bps,
        cost=FixedCost(
            schedule.name, "USD", FX_ABSOLUTE_ROUND_TRIP, hard, "row1_provisional"
        ),
    )
