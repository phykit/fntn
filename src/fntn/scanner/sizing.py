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
