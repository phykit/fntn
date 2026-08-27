"""Registered parameters: §13 rows 19, 20, 22 and 25, plus §14's two governance values.

**The scanner will not sweep without these.** Not as a nicety: a sweep whose
abandonment threshold, control-arm ratio and seed were chosen afterwards is a
sweep whose pass condition was set by someone who had already seen the result,
and no amount of later honesty repairs it. §7.5 applies the same discipline to
the placebo, and §3.6.8 step 4 to every directive.

The object is canonically serialised and hashed. The hash goes on every record
the run produces, so a reader can tell which registration a directive was raised
under, and a changed value produces a visibly different run rather than a quiet
one.

**What this file is not.** It is not the parameter object of §0.3, which covers
the whole design and whose hash creates frozen design 1. This is the discovery
layer's own registration, a strict subset, and it is named separately so the two
cannot be confused. Registering these does not advance the freeze.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .markets import CorpusInvalid, validate_corpus
from .records import RULEBOOK_STOPWORDS, ScoringMode


class RegistrationIncomplete(RuntimeError):
    """Raised rather than defaulted. See the module docstring."""


@dataclass(frozen=True)
class DiscoverableClass:
    """One row of §13 row 22: a class declared discoverable, and how.

    Declares *whether* a class may be discovered. It does not declare the
    exclusivity guarantee: that is a property of the corpus the proposal was
    read from, and lives on ``Corpus``.
    """

    event_class: str
    #: Free text: which markets carry this class. Recorded so a construction
    #: claim can be audited later. Advisory: the corpus decides the guarantee.
    external_markets: str = ""


@dataclass(frozen=True)
class Corpus:
    """One row of §13 row 22: a readable corpus.

    ``partition`` must be ``discovery`` or ``external``. Anything else is a
    scored population and reading it would make selection and evaluation share
    observations.
    """

    corpus_id: str
    market: str
    partition: str
    retrieval_route: str
    #: The exclusivity guarantee THIS CORPUS provides. A property of where the
    #: material was read, not of the class that was read from it: one event
    #: class discovered from an ASX corpus is cross_market and from an EDGAR
    #: corpus is pre_archive. An earlier version keyed this on the class, which
    #: made the guarantee unstateable for any class read from both.
    scoring_mode: Optional[str] = None


@dataclass
class Registration:
    """Everything the operator must commit before the first sweep."""

    # -- §13 row 19: the control arm's kill criterion ----------------------
    #: The separation below which the discovery layer is refuted, in the units
    #: the measurement reports. Committed blind: you are stating the magnitude
    #: worth pursuing before you know whether the answer flatters you.
    control_arm_delta: Optional[float] = None
    control_arm_delta_units: str = "bps"
    #: Minimum observations per arm below which the verdict is
    #: `undetermined_at_budget` rather than a quiet pass or a quiet kill.
    control_arm_n_min: Optional[int] = None

    # -- §13 row 20: the control arm's construction ------------------------
    #: Drawn mechanisms per proposed mechanism. Strictly above zero: a sweep
    #: with no control arm has no instrument that can refute it.
    control_arm_ratio: Optional[float] = None
    #: Recorded with every draw so the arm is replayable and cannot be redrawn
    #: once the treatment arm's result is known.
    control_arm_seed: Optional[int] = None

    # -- §13 row 22: what may be discovered, and from where ----------------
    corpora: List[Corpus] = field(default_factory=list)
    discoverable_classes: List[DiscoverableClass] = field(default_factory=list)
    default_scoring_mode: str = ScoringMode.CROSS_MARKET.value

    # -- §13 row 25: the security master -----------------------------------
    #: Paths to the master files. Coverage is measured by `master.py`.
    security_master_files: List[str] = field(default_factory=list)
    #: Share of listed entities per discovery market that must be present in
    #: the master before that market is readable. Below it, the fence has holes
    #: it cannot see and the market is refused.
    master_coverage_floor: float = 0.95

    # -- §13 row 21: the fence's own vocabulary ----------------------------
    #: Rulebook nouns that may head a legal-form span without a firm being
    #: named. Registered rather than left as a module constant because it
    #: changes what the entity fence refuses, and a value that changes what a
    #: fence refuses and does not reach the hash is a fence whose behaviour
    #: cannot be attributed to a registration. Adding a row here is a re-stamp,
    #: which is the point: it makes the cost of a quiet widening visible.
    rulebook_stopwords: List[str] = field(
        default_factory=lambda: sorted(RULEBOOK_STOPWORDS)
    )

    # -- the archive boundary that pre_archive is defined against ----------
    #: ISO date on which the archive opens. **Required when any corpus declares
    #: ``pre_archive``**, because without it that mode names no boundary and is
    #: a label rather than a guarantee.
    #:
    #: This is one of §13's pre-calibration fixings and it needs no purchase:
    #: it is a decision about which span the archive will cover, not an
    #: acquisition of it.
    archive_opens: Optional[str] = None

    # -- §14 governance ----------------------------------------------------
    #: Pairwise design-segment overlap tolerance.
    theta: Optional[float] = None
    #: Floor below which a directive is not worth a session of the segment.
    delta_min_floor: Optional[float] = None

    # -- provenance --------------------------------------------------------
    registered_at: Optional[str] = None
    registered_by: str = ""
    #: Free text: why these values and not others. Not read by anything; it
    #: exists because a number whose reasoning is not written down gets changed
    #: by whoever meets it next.
    rationale: str = ""

    # -- validation --------------------------------------------------------

    def missing(self) -> List[str]:
        """Everything absent, named. Reported all at once, not fail-fast.

        Registration spends no compute and its output is a worklist for a
        person; handing someone one blocker at a time when six are known is a
        worse deliverable rather than a purer one.
        """

        out: List[str] = []
        if self.control_arm_delta is None:
            out.append("control_arm_delta (§13 row 19)")
        if self.control_arm_n_min is None:
            out.append("control_arm_n_min (§13 row 19)")
        if self.control_arm_ratio is None:
            out.append("control_arm_ratio (§13 row 20)")
        elif self.control_arm_ratio <= 0:
            out.append("control_arm_ratio must exceed zero (§13 row 20)")
        if self.control_arm_seed is None:
            out.append("control_arm_seed (§13 row 20)")
        if not self.corpora:
            out.append("corpora (§13 row 22)")
        if not self.discoverable_classes:
            out.append("discoverable_classes (§13 row 22)")
        if not self.security_master_files:
            out.append("security_master_files (§13 row 25)")
        if self.theta is None:
            out.append("theta (§14 governance)")
        if self.delta_min_floor is None:
            out.append("delta_min_floor (§14 governance)")
        if not self.registered_at:
            out.append("registered_at")
        if not self.registered_by:
            out.append("registered_by")

        valid = {m.value for m in ScoringMode}
        if self.default_scoring_mode not in valid:
            out.append(
                f"default_scoring_mode {self.default_scoring_mode!r} is not one "
                f"of {sorted(valid)}"
            )

        for c in self.corpora:
            if c.partition not in ("discovery", "external"):
                out.append(
                    f"corpus {c.corpus_id!r} sits in partition {c.partition!r}, "
                    "which a discovery agent may not read"
                )
            mode = c.scoring_mode or self.default_scoring_mode
            if mode not in valid:
                out.append(
                    f"corpus {c.corpus_id!r} names scoring_mode {mode!r}, which "
                    f"is not one of {sorted(valid)}"
                )
            else:
                try:
                    validate_corpus(c.market, mode)
                except CorpusInvalid as exc:
                    out.append(f"corpus {c.corpus_id!r}: {exc}")
                if mode == "pre_archive" and not self.archive_opens:
                    out.append(
                        f"corpus {c.corpus_id!r} declares pre_archive but "
                        "archive_opens is not set: the mode is defined as "
                        "'material predating the archive's opening boundary', "
                        "so with no boundary it names nothing and the guarantee "
                        "is a label. Fixing the archive span is a §13 "
                        "pre-calibration decision and needs no purchase"
                    )
        if self.delta_min_floor is not None and self.control_arm_delta is not None:
            if self.control_arm_delta < self.delta_min_floor:
                out.append(
                    f"control_arm_delta ({self.control_arm_delta}) is below "
                    f"delta_min_floor ({self.delta_min_floor}): the layer's own "
                    "kill threshold cannot be smaller than the smallest effect "
                    "worth a session of the segment"
                )
        return out

    def require_complete(self) -> None:
        gaps = self.missing()
        if gaps:
            raise RegistrationIncomplete(
                "the discovery layer will not sweep until these are registered:\n  "
                + "\n  ".join(f"- {g}" for g in gaps)
                + "\n\nRegistering them after a sweep does not work: a kill "
                "criterion written once a result is known is not a kill "
                "criterion (§13 rows 19-20, §7.5)."
            )

    # -- identity ----------------------------------------------------------

    def hash(self) -> str:
        """Canonical hash. Goes on every record the run produces."""

        payload = asdict(self)
        payload.pop("rationale", None)  # prose, not a parameter
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def is_discoverable(self, event_class: str) -> bool:
        """Whether the class may be discovered at all (§13 row 22).

        Separate from the construction, which the corpus supplies. A class
        absent here is refused with `scoring_mode_unsatisfiable` whatever
        corpus raised it.
        """

        return any(c.event_class == event_class for c in self.discoverable_classes)

    def scoring_mode_for_corpus(self, corpus_id: str) -> Optional[str]:
        for c in self.corpora:
            if c.corpus_id == corpus_id:
                return c.scoring_mode or self.default_scoring_mode
        return None

    # -- persistence -------------------------------------------------------

    def save(self, path: str | Path) -> str:
        p = Path(path)
        p.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")
        return self.hash()

    @classmethod
    def load(cls, path: str | Path) -> "Registration":
        raw = json.loads(Path(path).read_text())
        raw["corpora"] = [Corpus(**c) for c in raw.get("corpora", [])]
        raw["discoverable_classes"] = [
            DiscoverableClass(**c) for c in raw.get("discoverable_classes", [])
        ]
        return cls(**raw)

    @classmethod
    def blank(cls) -> "Registration":
        """A form with the values left out, for the operator to fill.

        Deliberately not pre-populated with plausible numbers. A form arriving
        with defaults already in it is a form whose defaults get accepted.
        """

        return cls(
            registered_at=None,
            corpora=[],
            discoverable_classes=[],
            rationale="Why these values and not others. Required by nothing; "
            "read by whoever inherits this.",
        )

    def stamp(self, by: str) -> "Registration":
        """Fix `registered_at`. Call exactly once, before the first sweep."""

        if self.registered_at:
            raise RegistrationIncomplete(
                f"already registered at {self.registered_at}; re-stamping would "
                "move a timestamp whose whole purpose is that it cannot move"
            )
        self.registered_at = datetime.now(timezone.utc).isoformat()
        self.registered_by = by
        return self

    def render(self) -> str:
        lines = [
            "Discovery-layer registration",
            f"  hash                         : {self.hash()}",
            f"  registered_at                : {self.registered_at or 'NOT STAMPED'}",
            f"  registered_by                : {self.registered_by or 'n/a'}",
            f"  control arm delta            : {self.control_arm_delta} {self.control_arm_delta_units}",
            f"  control arm n_min            : {self.control_arm_n_min}",
            f"  control arm ratio / seed     : {self.control_arm_ratio} / {self.control_arm_seed}",
            f"  default scoring mode         : {self.default_scoring_mode}",
            f"  archive opens                : {self.archive_opens or 'NOT SET'}",
            f"  theta / delta_min floor      : {self.theta} / {self.delta_min_floor}",
            f"  corpora                      : {len(self.corpora)}",
        ]
        for c in self.corpora:
            lines.append(
                f"    {c.corpus_id} ({c.market}, {c.partition}) "
                f"-> {c.scoring_mode or self.default_scoring_mode} "
                f"via {c.retrieval_route}"
            )
        lines.append(f"  discoverable classes         : {len(self.discoverable_classes)}")
        for c in self.discoverable_classes:
            lines.append(
                f"    {c.event_class}"
                + (f"  [{c.external_markets}]" if c.external_markets else "")
            )
        gaps = self.missing()
        if gaps:
            lines.append(f"  INCOMPLETE: {len(gaps)} item(s) outstanding")
            lines.extend(f"    - {g}" for g in gaps)
        else:
            lines.append("  complete: the layer may sweep")
        return "\n".join(lines)
