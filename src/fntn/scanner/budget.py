"""The intake budget: a ceiling on time, decided once and never re-raced.

**What this is.** Three registered quantities, ``intake_point_budget_s``,
``intake_subject_budget_s`` and ``budget_retry_max``, and the machinery that
applies them.  A subject whose intake exceeds the ceiling is abandoned with
``intake_budget_exhausted`` rather than held open, because an intake that never
finishes consumes the surface it is standing on and nothing downstream can tell
it from one still running.

**THE DECISION IS TAKEN ONCE, AT CAPTURE, AND THE LEDGER HOLDS IT.**  This is
the whole of the design and everything else here serves it.  Rule 1 says every
number and verdict on the trading path is deterministic arithmetic over logged
data, replayable byte-for-byte from the parameter hash.  A clock is the exact
opposite of that: it returns a different answer every time it is asked, so a
replay that re-times the work would reproduce a *different* refusal set on the
same inputs, and the run would not be replayable at all.  A wall clock in a
replay path makes rule 1 false, quietly, on the one surface where the falsehood
is hardest to see.

So: :class:`MeasuringBudget` races the clock **once**, at capture, and writes
what it saw.  :class:`ReplayedBudget` reads those records and **never calls a
clock at all** -- it holds no clock to call, and
``test_a_replay_under_a_different_wall_clock_reproduces_the_decision`` gives it
one that raises if touched.

**The honest limit, stated rather than implied: this is a ceiling that refuses,
not a timeout that interrupts.**  A check is run and then measured.  Nothing
here preempts a call, so a point that blocks forever blocks forever and the
budget never fires; what the budget catches is work that finished late, not
work that never finished.  Preemption would need a thread or a signal per
check, which is apparatus of a different order, and it is not taken for a
refusal whose purpose is to stop a slow intake consuming a surface.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

#: The point at which a subject's own cumulative budget is charged, as opposed
#: to any single check's.  Not a check name, and deliberately not one that could
#: collide with one, because it must never be read as an intake position.
SUBJECT_POINT = "__subject__"


class BudgetReplayError(RuntimeError):
    """A replay was asked for a decision the capture never recorded.

    Refused rather than re-measured. Re-measuring would substitute a fresh
    clock reading for a missing record, which is precisely the substitution
    this module exists to prevent, and it would do it silently.
    """


@dataclass(frozen=True)
class BudgetDecision:
    """One decision, as taken at capture.  The ledger's unit and the replay's.

    ``elapsed_s`` and ``budget_s`` are recorded beside ``exhausted`` so a reader
    can see *why* rather than only *what*, and so a later budget change can be
    checked against what actually happened rather than re-run against it.
    ``at`` is recorded here too, so the refusal a replay emits carries the
    capture's timestamp and not the replay's.
    """

    subject_id: str
    point: str
    elapsed_s: float
    budget_s: float
    attempts: int
    exhausted: bool
    at: str

    def as_fields(self) -> Dict[str, object]:
        """The §8 template's inputs, rendered from the record's own fields."""

        return {
            "point": self.point,
            "elapsed_s": f"{self.elapsed_s:.3f}",
            "budget_s": f"{self.budget_s:.3f}",
            "attempts": self.attempts,
            "attempted_at": self.at,
        }


@dataclass
class MeasuringBudget:
    """Races the clock once, at capture, and records what it saw.

    ``retry_max`` is the number of *further* attempts a point gets after an
    over-run, so 1 means two attempts in total.  A retry is offered because the
    commonest cause of a single slow point is a source that was briefly
    unavailable, and refusing an idea for that would be refusing the source's
    weather rather than the idea.  Every attempt is counted and recorded, so a
    point that only ever passes on its second attempt is visible rather than
    indistinguishable from one that passes first time.
    """

    point_budget_s: float
    subject_budget_s: float
    retry_max: int = 1
    #: Injected so the tests can drive it. In production it is a monotonic
    #: clock, because a wall clock can step backwards and a negative elapsed
    #: time would read as comfortably within budget.
    clock: Callable[[], float] = time.monotonic
    decisions: List[BudgetDecision] = field(default_factory=list)
    _subject_start: Dict[str, float] = field(default_factory=dict)
    _subject_elapsed: Dict[str, float] = field(default_factory=dict)

    replaying = False

    def start_subject(self, subject_id: str) -> None:
        self._subject_start[subject_id] = self.clock()
        self._subject_elapsed[subject_id] = 0.0

    def _record(self, **kw) -> BudgetDecision:
        d = BudgetDecision(at=datetime.now(timezone.utc).isoformat(), **kw)
        self.decisions.append(d)
        return d

    def run_point(
        self, subject_id: str, point: str, fn: Callable[[], object]
    ) -> Tuple[object, BudgetDecision]:
        """Run the check, then measure it.  Retry on an over-run, then refuse."""

        attempts = 0
        elapsed = 0.0
        result = None
        while attempts <= self.retry_max:
            attempts += 1
            t0 = self.clock()
            result = fn()
            elapsed = self.clock() - t0
            if elapsed <= self.point_budget_s:
                break
        self._subject_elapsed[subject_id] = (
            self._subject_elapsed.get(subject_id, 0.0) + elapsed
        )
        return result, self._record(
            subject_id=subject_id,
            point=point,
            elapsed_s=elapsed,
            budget_s=self.point_budget_s,
            attempts=attempts,
            exhausted=elapsed > self.point_budget_s,
        )

    def check_subject(self, subject_id: str) -> BudgetDecision:
        elapsed = self._subject_elapsed.get(subject_id, 0.0)
        return self._record(
            subject_id=subject_id,
            point=SUBJECT_POINT,
            elapsed_s=elapsed,
            budget_s=self.subject_budget_s,
            attempts=1,
            exhausted=elapsed > self.subject_budget_s,
        )


@dataclass
class ReplayedBudget:
    """Reads the recorded decisions.  **Holds no clock and calls none.**

    The absence of a clock is not an optimisation and not a convenience: it is
    the property that makes a replay a replay. A budget that re-timed the work
    would produce a different refusal set from the same inputs on a busier
    machine, and every figure derived from that run would be a figure the
    parameter hash does not determine.
    """

    decisions: Sequence[BudgetDecision]
    replaying = True

    def __post_init__(self) -> None:
        self._by_key: Dict[Tuple[str, str], List[BudgetDecision]] = {}
        for d in self.decisions:
            self._by_key.setdefault((d.subject_id, d.point), []).append(d)
        self._used: Dict[Tuple[str, str], int] = {}

    def _take(self, subject_id: str, point: str) -> BudgetDecision:
        key = (subject_id, point)
        seen = self._used.get(key, 0)
        rows = self._by_key.get(key, [])
        if seen >= len(rows):
            raise BudgetReplayError(
                f"no recorded budget decision for {subject_id} at {point!r}. "
                "Refusing to take a fresh clock reading in its place: a replay "
                "that measures is not a replay, and substituting one here would "
                "make the run's refusal set depend on the machine it was "
                "replayed on."
            )
        self._used[key] = seen + 1
        return rows[seen]

    def start_subject(self, subject_id: str) -> None:
        return None

    def run_point(
        self, subject_id: str, point: str, fn: Callable[[], object]
    ) -> Tuple[object, BudgetDecision]:
        # The check itself is re-run, because it is deterministic arithmetic
        # over the subject and reproduces its own verdict. Only the timing is
        # taken from the record, because only the timing is not.
        return fn(), self._take(subject_id, point)

    def check_subject(self, subject_id: str) -> BudgetDecision:
        return self._take(subject_id, SUBJECT_POINT)


def decisions_to_rows(decisions: Iterable[BudgetDecision]) -> List[Dict[str, object]]:
    """For the ledger.  Elapsed time, the budget in force, and the decision."""

    return [asdict(d) for d in decisions]


def decisions_from_rows(rows: Iterable[Dict[str, object]]) -> List[BudgetDecision]:
    return [BudgetDecision(**r) for r in rows]
