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
from dataclasses import asdict, dataclass, field, fields as dc_fields
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import ClassVar, Dict, List, Optional

from .markets import CorpusInvalid, validate_corpus
from .records import RULEBOOK_STOPWORDS, SEED_LEXICON, ScoringMode


class RegistrationIncomplete(RuntimeError):
    """Raised rather than defaulted. See the module docstring."""


class RegistrationHashMismatch(RuntimeError):
    """A stored registration does not hash to the hash it records.

    Raised only where the two are actually comparable, that is where the file's
    schema fingerprint matches the current one. Across a schema change the
    recomputation answers a different question and the state is
    ``unverifiable_schema_change``, which is reported and never called
    verification.
    """


class RegistrationHistoryMissing(RuntimeError):
    """A stamped registration was about to be overwritten unrecorded.

    Rule 4 says nothing in the ledger is deleted and nothing is overwritten. The
    registration was exempt from its own rule: ``save`` wrote over whatever was
    already at the path, so a re-stamp destroyed the object the previous hash
    was taken over and left the hash on records that nothing could be replayed
    against. Recording the prior hash in the history file is the price of the
    overwrite.
    """


#: Where the chain of superseded hashes lives, relative to the registration
#: file's own directory. Named as a path fragment rather than a repository
#: constant so a registration saved somewhere else looks for its history beside
#: itself rather than in a tree it has nothing to do with.
HISTORY_FILE = Path("docs") / "REGISTRATION_HISTORY.md"

#: What a schema fingerprint is written as. **The prefix types the value; it is
#: not part of the digest and reaches neither hash.**
#:
#: *Why it exists.* The fingerprint was stored as sixteen hex characters, which
#: is exactly the shape of a registration hash, so the two were
#: indistinguishable to anything reading the file mechanically. A sweep of
#: `discovery_registration.json` for registration hashes found two values and
#: had to be told by a person that one of them was not a stamp, which is a
#: check that is not machine-checkable and therefore, by this project's own
#: standard, not a check. Prefixing makes the stored token `schema:<digest>`,
#: which no sweep for a hash can read as one.
#:
#: **The cost, stated.** A naked `[0-9a-f]{16}` regex ignores token boundaries
#: and still matches the digest inside the prefixed value, so the prefix types
#: the record and does not on its own repair a careless sweep. The sweep is
#: therefore written down beside the record it sweeps, in
#: `docs/REGISTRATION_HISTORY.md`, and `test_a_hash_sweep_of_the_registration_
#: finds_only_registration_hashes` is what holds it rather than the prose.
SCHEMA_PREFIX = "schema:"


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

    def __post_init__(self) -> None:
        """Refuse a route into an underscore-prefixed directory.

        **Underscore-prefixed means bookkeeping or fenced material, never
        corpus.** `corpora/us/_raw` holds the pages the server sent;
        `corpora/_trace_filings` holds SEC Form 4 filings for the §9.4
        harness, which **name issuers and dates and are exactly what the
        entity fence exists to keep out of a proposal**.

        **Refused here and not in `missing()`, because `missing()` returns
        advice and advice is not a fence.** A registration naming such a route
        must be *unconstructible*, so that a file naming it will not load at
        all rather than loading with a warning nobody reads. Any component of
        the path is checked, not merely the last: `corpora/_trace_filings/2026`
        reaches the same material one level down.
        """

        parts = PurePosixPath(str(self.retrieval_route).strip()).parts
        for part in parts:
            if part.startswith("_"):
                raise CorpusInvalid(
                    f"corpus {self.corpus_id!r} names retrieval_route "
                    f"{self.retrieval_route!r}, whose component {part!r} is "
                    "underscore-prefixed. Underscore-prefixed directories are "
                    "bookkeeping or fenced material and are never corpus: "
                    "corpora/us/_raw holds raw pages, and "
                    "corpora/_trace_filings holds filings that name issuers "
                    "and dates, which is the material the entity fence exists "
                    "to keep out of a proposal. A corpus is what the agent is "
                    "shown, so a route that can reach either is a fence with "
                    "a door in it."
                )


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
    #: The regulatory lexicon: tokens that are entity-shaped and are not
    #: entities. Here for the same reason as ``rulebook_stopwords`` and one
    #: level up: it decides what the fence ignores, and it also decides what
    #: the master loader lets into the ticker set, so two runs under one hash
    #: could otherwise refuse two different things. It was a module constant
    #: until the 27 August re-stamp, and the specification recorded that as a
    #: known defect rather than fixing it silently; this is the fix.
    #:
    #: Adding a row is therefore a re-stamp. That is the cost, and it is the
    #: point: a row added quietly widens what a sweep lets through with nothing
    #: on the record.
    lexicon: List[str] = field(default_factory=lambda: sorted(SEED_LEXICON))

    # -- §13 row 27: the intake budget -------------------------------------
    #: Seconds one intake point may take before the subject is abandoned with
    #: `intake_budget_exhausted`.
    #:
    #: **Registered because it changes what a run refuses.** Two sweeps over
    #: one corpus under one hash could otherwise abandon different subjects,
    #: and the difference would be attributable to nothing on the record.
    #:
    #: **The decision it drives is taken once, at capture, and the ledger holds
    #: it.** A replay reads the recorded elapsed time and never re-times the
    #: work: a clock in the replay path would make the refusal set depend on
    #: the machine, which is rule 1 made false on the surface where it is
    #: hardest to see. See `budget.py`.
    intake_point_budget_s: float = 20.0
    #: Seconds the whole of one subject's intake may take, cumulatively.
    #: Separate from the point budget because twelve points each comfortably
    #: inside their own ceiling can still add to an intake nobody would run.
    intake_subject_budget_s: float = 120.0
    #: Further attempts a point gets after an over-run. 1 means two attempts in
    #: total. Offered because the commonest cause of one slow point is a source
    #: briefly unavailable, and refusing an idea for that refuses the source's
    #: weather rather than the idea. Every attempt is counted and recorded.
    budget_retry_max: int = 1

    # -- §7.2: the audit fraction ------------------------------------------
    #: Share of subjects that run the **full panel** regardless of early
    #: failures, so that the reason-code distribution is not censored by
    #: fail-fast. §7.2's antidote to that censoring, and **every attribution
    #: statistic computes on the audit sample exclusively**.
    #:
    #: **Registered on 27 August 2026 because §7.2 already called it
    #: "pre-registered" and it was not registered at all.** It was a default
    #: argument in `ingest.py` and `run.py`, so two runs under one parameter
    #: hash could audit different fractions and the difference would be
    #: attributable to nothing on the record. That is the third instance of the
    #: defect class that caused the `rulebook_stopwords`, `lexicon` and intake
    #: budget re-stamps, and `docs/CORRECTIONS.md` records why closing three
    #: instances did not close the class.
    #:
    #: **The sample was always replayable and the fraction was not.** The audit
    #: draw is a hash of the subject identity and the parameter hash, so a given
    #: fraction always selects the same subjects; nothing recorded which
    #: fraction had been in force.
    audit_fraction: float = 0.10

    # -- §13 row 29: the maximum tolerable fixed cost ----------------------
    #: Basis points of position, round trip, **excluding spread and market
    #: impact**, neither of which has a §13 row and both of which scale with
    #: participation.
    #:
    #: **Registered because it decides which names exist.** It is the one free
    #: parameter §13 row 30's clip-floor derivation cannot eliminate, and every
    #: per-market floor beneath it is arithmetic. Two runs under one hash could
    #: otherwise size against two different tolerances and admit two different
    #: universes, and the difference would be attributable to nothing.
    #:
    #: **Dimensionless on purpose.** One number governs a USD and a GBP trade
    #: with no FX rate entering a governance decision, it is comparable across
    #: markets, and §5.2.2 and §0.5 are already in basis points so it can be
    #: read straight off the break-even table.
    #:
    #: **Set to 10.0 on 27 August 2026 on delegated authority**, inside a range
    #: whose ends are both derived: 2.375 bp below, where `104/p` exceeds the
    #: tolerance and no position size of any kind reaches it, and 12.5 bp
    #: above, which is the fixed-cost basis §5.2.2's cheapest break-even was
    #: computed on. The operator's standing right to revise is unaffected, and
    #: **revising to 12.5 is the decision about whether the UK exists**.
    max_tolerable_fixed_cost_bps: Optional[float] = None

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
    #: The hash this object was stamped under, written by ``save`` and excluded
    #: from the hash itself.
    #:
    #: **Why the file has to say.** A hash is taken over the dataclass as well
    #: as the values, so a stored registration stops recomputing to its own
    #: hash the moment a field is added: the 26 August object hashes to
    #: `a06400ef28ebb54c` under the schema it was stamped under and to
    #: something else under every schema since, and it is the same file. The
    #: first row of ``docs/REGISTRATION_HISTORY.md`` is a reconstruction for
    #: exactly that reason, and every row there needs its own commit's code to
    #: recompute. A file that carries its own hash needs neither.
    registered_hash: Optional[str] = None
    #: The shape the hash was taken over, written by ``save`` beside the hash
    #: and excluded from the hash for the same reason.
    #:
    #: **Why a fingerprint and not just the hash.** A recomputation can only
    #: check a stored hash whilst the dataclass is the one it was taken under.
    #: Add a field and every registration on disk stops hashing to its own
    #: recorded hash, all at once and with nothing wrong. Without the
    #: fingerprint there is no way to tell that case from a tampered file, so
    #: the choice is between verifying nothing and raising on every old file,
    #: and both are wrong. With it the two are distinguishable and the third
    #: state, *cannot verify*, can be reported as itself.
    #:
    #: **Written as `schema:<digest>`, never as a bare digest.** Untyped it was
    #: sixteen hex characters, the shape of a registration hash, and a sweep of
    #: this file for unrecorded stamps found it and could only be told by hand
    #: that it was not one. See `SCHEMA_PREFIX`.
    registered_schema: Optional[str] = None
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
        for name in ("intake_point_budget_s", "intake_subject_budget_s"):
            value = getattr(self, name)
            if value is None or value <= 0:
                out.append(
                    f"{name} must exceed zero (§13 row 27): a ceiling of zero "
                    "abandons every subject before any check runs, which is a "
                    "refusal of the whole surface wearing a budget's clothes"
                )
        if self.intake_subject_budget_s and self.intake_point_budget_s:
            if self.intake_subject_budget_s < self.intake_point_budget_s:
                out.append(
                    "intake_subject_budget_s is below intake_point_budget_s "
                    "(§13 row 27): a subject may not be given less time than "
                    "one of its own points"
                )
        if self.budget_retry_max is None or self.budget_retry_max < 0:
            out.append("budget_retry_max must be zero or more (§13 row 27)")
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

    #: What ``load`` was able to establish about the file it read. NOT a
    #: dataclass field, deliberately: it describes the reading and not the
    #: registration, so it must stay out of ``asdict`` and out of the hash.
    #:
    #: ``not_loaded`` is the default because an object built in memory was
    #: never read from anything and has nothing to verify against. The state
    #: that matters is ``unverifiable_schema_change``, which exists so that
    #: *cannot verify* is a value a reader can see rather than the silence that
    #: *verified* also produces.
    UNSTAMPED: ClassVar[str] = "unstamped"
    VERIFIED: ClassVar[str] = "verified"
    UNVERIFIABLE: ClassVar[str] = "unverifiable_schema_change"
    hash_verification: ClassVar[str] = "not_loaded"

    @classmethod
    def schema_fingerprint(cls) -> str:
        """A digest of the shape the hash is taken over. Not of the values.

        Covers exactly what ends up in the hashed payload: this class's field
        names less the provenance fields ``hash`` discards, plus the field
        names of the two nested dataclasses, whose shapes reach the payload
        through ``asdict``. Names only, sorted, because ``hash`` serialises
        with ``sort_keys`` and so depends on the set of keys and not their
        order.

        A field added to the payload changes this; a provenance field added
        beside it changes neither this nor the hash, which is the whole reason
        the two exclusions are shared.
        """

        excluded = {"rationale", "registered_hash", "registered_schema"}
        shape = {
            "registration": sorted(
                f.name for f in dc_fields(cls) if f.name not in excluded
            ),
            "corpus": sorted(f.name for f in dc_fields(Corpus)),
            "discoverable_class": sorted(f.name for f in dc_fields(DiscoverableClass)),
        }
        blob = json.dumps(shape, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
        return SCHEMA_PREFIX + digest

    @classmethod
    def schema_matches(cls, stored: Optional[str]) -> bool:
        """Whether `stored` names the shape the dataclass currently has.

        **Two encodings are accepted and they denote the same shape.** The
        typed `schema:<digest>` is what `save` writes. A bare `<digest>` is the
        superseded encoding, written by every file stamped before the prefix
        landed, and it is the same digest of the same field names.

        *Why accepting it is the honest answer and not a fallback.* Rule 3
        forbids substituting a working value for a broken one. Nothing is
        substituted here: a bare digest equal to today's digest establishes
        that the file was stamped under today's field names, which is the only
        question this method asks. Refusing it would report
        `unverifiable_schema_change` over a file whose shape demonstrably
        matches, and *cannot verify* said of something that can be verified is
        as false as *verified* said of something that cannot.

        **The cost, stated.** A file still carrying the untyped encoding is
        still a sixteen-hex token in a sweep until it is next saved. `save`
        writes the typed form unconditionally, so the untyped encoding leaves
        the tree the first time each file is re-stamped and not before.
        """

        if not stored:
            return False
        current = cls.schema_fingerprint()
        return stored in (current, current[len(SCHEMA_PREFIX):])

    def hash(self) -> str:
        """Canonical hash. Goes on every record the run produces."""

        payload = asdict(self)
        payload.pop("rationale", None)  # prose, not a parameter
        # Self-referential: it records the result of this function, so hashing
        # it would make the value depend on itself.
        payload.pop("registered_hash", None)
        # And the fingerprint describes the shape of what is left, so it cannot
        # be part of what is left. Both being outside the payload is what makes
        # adding a provenance field move neither the hash nor the fingerprint,
        # which is the behaviour a provenance field ought to have.
        payload.pop("registered_schema", None)
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

    def save(
        self,
        path: str | Path,
        history: str | Path | None = None,
        prior_hash: Optional[str] = None,
    ) -> str:
        """Write the registration. Refuses to overwrite a stamped one unrecorded.

        **Why this is not a plain write.** Rule 4 says nothing is deleted and
        nothing is overwritten, and the registration was exempt from its own
        rule: a re-stamp destroyed the object the previous hash was taken over,
        so records already carrying that hash pointed at a file that no longer
        existed in any form a reader could recover. Two re-stamps had happened
        before this check existed, and the object behind the first of them is a
        reconstruction in ``docs/REGISTRATION_HISTORY.md`` rather than a
        recovery, no commit carrying it.

        The overwrite is therefore conditional on the prior version being
        written down first: its hash, on a line that also names the file it was
        the hash of, in the history document beside the registration. This is a
        *precondition*, not a side effect. ``save`` does not append the row
        itself, because a record written automatically by the step it is meant
        to constrain records only that the step ran.

        Refused rather than defaulted wherever the prior version cannot be
        shown to be on the record. A prior file that will not parse, and a
        prior file that does not say which hash it was stamped under, are both
        refusals: a hash that cannot be established cannot be looked for, and
        the alternative is to overwrite the file on the grounds that we could
        not read it.

        ``prior_hash`` is the operator stating that hash for a file written
        before ``registered_hash`` existed. It is an assertion, not a default:
        the history document must still corroborate it, and where the file does
        say, a disagreeing assertion is refused rather than preferred.
        """

        p = Path(path)
        hist = Path(history) if history is not None else p.parent / HISTORY_FILE

        prior = self._prior_hash(p, stated=prior_hash)
        if prior is not None and prior != self.hash():
            text = hist.read_text() if hist.exists() else ""
            if not any(prior in line and p.name in line for line in text.splitlines()):
                raise RegistrationHistoryMissing(
                    f"{p} holds a stamped registration whose hash is {prior}, "
                    f"and writing {self.hash()} over it would destroy the "
                    f"object that hash was taken over.\n\n"
                    f"Append a row naming both {prior} and {p.name} to {hist} "
                    "first, then save. Nothing is overwritten (rule 4), and a "
                    "registration is not exempt from the rule it exists to "
                    "serve."
                )

        self.registered_hash = self.hash()
        self.registered_schema = self.schema_fingerprint()
        p.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")
        return self.hash()

    @staticmethod
    def _prior_hash(p: Path, stated: Optional[str] = None) -> Optional[str]:
        """The hash of what is already at ``p``, or None if nothing is at risk.

        None means there is nothing there, or what is there was never stamped
        and is therefore a blank form rather than a commitment.

        The hash is **read from the file, not recomputed from it.** Recomputing
        would answer a different question: what this file would hash to under
        today's dataclass, which for every registration written before the last
        schema change is not the hash it was registered under and not the hash
        any record carries.
        """

        if not p.exists():
            return None
        try:
            prior = Registration.load(p)
        except Exception as exc:
            raise RegistrationHistoryMissing(
                f"{p} exists but will not load under the current schema "
                f"({exc}). Its hash therefore cannot be established, so it "
                "cannot be checked against the history, so it cannot be "
                "overwritten. Record it by hand in the history document and "
                "move the file aside deliberately."
            ) from exc
        if not prior.registered_at:
            return None
        if prior.registered_hash:
            if stated and stated != prior.registered_hash:
                raise RegistrationHistoryMissing(
                    f"{p} records its hash as {prior.registered_hash}; "
                    f"prior_hash was given as {stated}. The file is the "
                    "record and the assertion is not, so the disagreement is "
                    "refused rather than resolved in favour of either."
                )
            return prior.registered_hash
        if stated:
            return stated
        raise RegistrationHistoryMissing(
            f"{p} was stamped at {prior.registered_at} and does not record the "
            "hash it was stamped under, so what would be overwritten cannot be "
            "named.\n\n"
            "Recomputing it here would give what the file hashes to under "
            "today's dataclass, which is a different number from the one its "
            "records carry whenever a field has been added since. Pass "
            "prior_hash=... with the hash from docs/REGISTRATION_HISTORY.md, "
            "which the history must then corroborate."
        )

    @classmethod
    def load(cls, path: str | Path) -> "Registration":
        """Read a registration, and establish what can be established about it.

        **Until this checked, nothing did.** A file whose ``registered_hash``
        disagreed with its own contents loaded silently, and ``save``'s
        overwrite guard reads that recorded hash as the identity of what it is
        about to destroy: an edited hash would have released the guard against
        a history row for an object that was never on disk.

        Three outcomes, and the third is the one worth having:

        * **no recorded hash** -- ``unstamped``. A blank form or a file written
          before the field existed. Nothing to verify, and nothing claimed.
        * **fingerprint matches** -- the recomputation is comparable, so it is
          performed. Equal is ``verified``; unequal raises
          ``RegistrationHashMismatch``, because at that point the file is
          wrong rather than merely old.
        * **fingerprint absent or different** --
          ``unverifiable_schema_change``. The hash is taken over the dataclass
          as well as the values, so a recomputation under a different shape
          answers a different question and its disagreement means nothing.
          **The file loads and no verification is claimed.** Raising here would
          make every registration written before this landed unreadable,
          including the two the history's own test replays; passing silently
          would let *cannot verify* read as *verified*, which is the failure
          this whole exercise is about.
        """

        raw = json.loads(Path(path).read_text())
        raw["corpora"] = [Corpus(**c) for c in raw.get("corpora", [])]
        raw["discoverable_classes"] = [
            DiscoverableClass(**c) for c in raw.get("discoverable_classes", [])
        ]
        obj = cls(**raw)

        if not obj.registered_hash:
            obj.hash_verification = cls.UNSTAMPED
        elif not cls.schema_matches(obj.registered_schema):
            obj.hash_verification = cls.UNVERIFIABLE
        else:
            recomputed = obj.hash()
            if recomputed != obj.registered_hash:
                raise RegistrationHashMismatch(
                    f"{path} records its hash as {obj.registered_hash} and "
                    f"hashes to {recomputed}, under the schema it was written "
                    f"under ({obj.registered_schema}). The values have been "
                    "changed since it was stamped, or the recorded hash has. "
                    "Either way the file no longer describes the object any "
                    "record carrying that hash was raised under."
                )
            obj.hash_verification = cls.VERIFIED
        return obj

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
            f"  hash verification            : {self.hash_verification}",
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
