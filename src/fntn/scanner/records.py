"""Record types for the agent discovery scanner.

Spec: From Narrative to Null v1.14 (proposed), §3.6.2, §3.7.

The types here draw the authority boundaries the architecture rests on.  A
``Proposal`` is the whole of what a discovery agent may emit; an ``IntakeRecord``
is what the deterministic path constructs from it; a ``Directive`` is what the
operator registers.  Fields the agent may not populate are absent from
``Proposal`` entirely rather than present and validated, because a field that
exists can be filled by a future caller who has forgotten why it was reserved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Sequence


class Origin(str, Enum):
    """Extends v1.11's ``origin`` enum (P50) with two machine origins.

    ``AGENT`` and ``RANDOM_CONTROL`` are siblings by construction: the control
    arm exists to be identical to the agent arm in every respect except the
    thing being tested, which is whether the agent's selection carries
    information.
    """

    PAPER = "paper"
    OPERATOR = "operator"
    AGENT = "agent"
    RANDOM_CONTROL = "random_control"


class EvidenceTier(str, Enum):
    QUANTIFIED = "quantified"
    POINTER = "pointer"


class Provenance(str, Enum):
    VERIFIED_PRIMARY = "verified_primary"
    VERIFIED_SECONDARY = "verified_secondary"
    RECOLLECTION = "recollection"
    #: Evidence produced by a directive this system raised.  Routes
    #: advisory-only under §3.6.3 check 5, exactly as ``single_study`` does.
    SELF_GENERATED = "self_generated"
    AGENT_GENERATED = "agent_generated"


class StreamStatus(str, Enum):
    SUBSCRIBED = "subscribed"
    CATEGORY_FILTER = "category_filter"
    MANUAL_OBSERVATION = "manual_observation"
    NEW_SUBSCRIPTION = "new_subscription"


class StreamProvenance(str, Enum):
    TABLE = "table"
    OPERATOR_MAPPED = "operator_mapped"


class ScoringMode(str, Enum):
    """Which exclusivity guarantee separates finding from evaluation.

    Recorded on every directive and printed beside every verdict.  §Σ.3's
    population-declaration surface applied to the exclusivity claim itself: a
    verdict answers *did what I measured pass*, and this field answers *what
    kept the finder out of the measurement*.
    """

    #: The agent read only markets outside §0.7(f).  Return paths are disjoint
    #: at zero cost in archive span.  **The assumption**: a mechanism observed
    #: under one market's disclosure regime holds under another's.
    CROSS_MARKET = "cross_market"
    #: The agent read in-universe material **predating the archive's opening
    #: boundary**.  Disjoint in time rather than in market, and free: the
    #: archive does not reach back that far, so the two share no observation.
    #:
    #: Split out from ``cross_market`` in v1.13 because the two rest on
    #: different assumptions with different failure modes.  Cross-market assumes
    #: mechanisms generalise across disclosure regimes; this assumes they are
    #: stable over time within one.  §0.7(a) records that the archive sits
    #: entirely inside the post-collapse regime, and Brochet's disclosure-speed
    #: finding is direct evidence that a regime moves, so this is not the weaker
    #: assumption by default and is measured on its own terms rather than under
    #: the cross-market generalisability row.
    #:
    #: **What enforces it, and what does not.**  ``archive_opens`` is required
    #: before this mode may be declared, so the boundary is stated rather than
    #: implied.  Nothing checks the date of each document in the corpus folder:
    #: the guarantee rests on the operator having put only pre-boundary material
    #: there.  That is a curation control, not a mechanical one, and saying so
    #: is the difference between a guarantee and a label.
    PRE_ARCHIVE = "pre_archive"
    #: The agent read only the Discovery partition; Gate 0 asserts separation
    #: from design, calibration and evaluation.  Stricter, and it costs span.
    DISJOINT_PARTITION = "disjoint_partition"
    #: The agent read in-universe material, so the directive scores only on
    #: items dated after ``registered_at``.  Disjoint in time, and slow.
    FORWARD_ONLY = "forward_only"


class Partition(str, Enum):
    DISCOVERY = "discovery"
    DESIGN = "design"
    CALIBRATION = "calibration"
    EVALUATION = "evaluation"
    #: Outside the archive entirely: non-universe markets, or material
    #: predating the archive's opening boundary.
    EXTERNAL = "external"


#: Partitions a discovery agent may read.  Everything else is a scored
#: population and reading it would make selection and evaluation share
#: observations.
READABLE_BY_DISCOVERY = frozenset({Partition.DISCOVERY, Partition.EXTERNAL})


class Verdict(str, Enum):
    PROMOTED = "promoted"
    KILLED_NEGLIGIBLE = "killed_negligible"
    UNDETERMINED_AT_BUDGET = "undetermined_at_budget"


# ---------------------------------------------------------------------------
# Entity detection -- the structural fence.
# ---------------------------------------------------------------------------

#: Instrument identifier formats.  These are closed, checkable grammars rather
#: than open vocabularies, so a pattern is the right instrument for them.
_IDENTIFIER_PATTERNS: Sequence[re.Pattern] = (
    re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}\d\b"),          # ISIN
    re.compile(r"\b[A-Z]{1,4}:[A-Z0-9.]{1,6}\b"),      # exchange-prefixed ticker
    re.compile(r"\(\s*(?:ticker|symbol)\s*:?\s*[A-Z0-9.]{1,6}\s*\)", re.I),
)

#: Bare tickers in running prose.  A ticker is a *symbol*, and the shape a
#: symbol takes on the page is the whole of what separates it from an ordinary
#: word: three or more characters, all capitals.  Two characters is too short to
#: carry the signal (``FR``, ``IT``, ``ON``), and any other case is a word
#: (``Note``, ``All``, ``Now``).  Exchange-prefixed and explicitly labelled forms
#: are already caught above, so this pattern carries only the bare case.
_BARE_TICKER_PATTERN = re.compile(r"\b[A-Z]{3,6}\b")

#: The shape a proper noun takes as the leading token of a designator span:
#: an initial capital, at least two characters, and letters throughout.  A bare
#: initial (``A Ltd``), a section number (``16a Holdings``) and punctuation are
#: excluded.  It is a cheap guard rather than the discriminating test; the
#: rulebook stopword set below is what actually separates a heading from a firm.
_PROPER_NOUN_LEAD = re.compile(r"[A-Z][A-Za-z&.'-]*[A-Za-z]$")

#: Corporate designators.  A designator is a strong signal because it is a
#: legal-form suffix that only ever attaches to a named firm; a regulator, a
#: rulebook and an exchange never carry one.
_DESIGNATOR_PATTERN = re.compile(
    r"\b[A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]*){0,4}\s+"
    r"(?:plc|PLC|Plc|Inc\.?|Ltd\.?|Limited|Corp\.?|Corporation|Holdings|"
    r"N\.V\.|S\.A\.|AG|GmbH|SE|AB|ASA|NV|SA)\b"
)

#: Date shapes.  Retained for *context only*: see ``entity_mentions``.
_DATE_PATTERNS: Sequence[re.Pattern] = (
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{4}\b"
    ),
    re.compile(r"\bQ[1-4]\s*(?:20)?\d{2}\b"),
)


@dataclass(frozen=True)
class EntityFence:
    """Detects episode-level content in a proposal.

    **This replaces a pattern-only detector that did not work.**  The first
    version flagged any two-to-five-letter capitalised token and any bare
    four-digit year, on the theory that bluntness was the safe direction.  A
    specification trace over thirty-six proposals drawn from real ASX, SEDI and
    MAR primary sources refused thirty-four of them, a 94% false-positive rate,
    with no true positives among the refusals.  It tripped on ``ASX``, ``TSX``,
    ``MAR``, ``SEDI``, ``ESMA``, ``UMIR``, ``DAX`` and on the years inside
    regulatory citations, because **a regulator's name and an issuer's name are
    both proper nouns and a regex cannot separate them.**

    The repair is the architecture's own principle rather than a better regex:
    *the model classifies, the table decides.*  A tradeable entity is a member
    of an enumerable set, namely the security master and the listing lists of
    the discovery markets, so the binding check is a **lookup against a closed
    list** and not a pattern over an open vocabulary.  Patterns are retained
    only where the grammar really is closed: instrument identifiers, and legal
    -form designators that attach to firms and never to regulators.

    **Dates are not independently episodic.**  An episode is an entity bound to
    a time; a mechanism that refers to a regulatory calendar, a review month or
    a statutory deadline is doing its job.  Dates are therefore reported as
    context beside an entity hit and never as a hit on their own, which is what
    removes the largest single source of the false-positive rate.

    **Tickers are held apart from names, because a symbol is not a word.**  A
    trace over the US corpus put 257 hits across thirteen documents, essentially
    all of them false, on ``Law``, ``Are``, ``For``, ``Help``, ``Note``, ``Any``,
    ``Such``, ``When`` and the single letters ``B``, ``C``, ``D``, ``E``, ``F``,
    ``H``, ``J``.  Every one came from the ticker half of the lookup: 7,268 of
    the 10,388 US tickers are four characters or fewer, and the loader's
    minimum-length and lexicon filters are applied to issuer names only, so the
    ticker set entered the fence unfiltered and sentence-initial capitalisation
    was enough to trip it.  A bare ticker therefore matches only in the shape a
    symbol takes: **all capitals, three characters or more** (see
    ``_BARE_TICKER_PATTERN``).  Names keep the span lookup unchanged, which is
    why the two sets are separate fields rather than one: sixty-five US issuers
    have a one-word name identical to their own ticker (``Ball``, ``Dole``,
    ``Coty``, ``Angi``), and merging the sets would have made the stricter
    ticker rule govern their names as well.

    **The cost, stated rather than implied.**  A bare ticker written in lower
    case or title case is now invisible to the fence: ``purchases at Aapl`` and
    ``purchases at aapl`` pass where ``purchases at AAPL`` is refused.  That is
    a false negative, and false negatives are the expensive direction, paid in
    the exclusivity guarantee rather than in a re-raise.  It is accepted here
    because the alternative measured worse: an unfiltered ticker set refuses
    ordinary English at a rate that would silently shape the search to whatever
    survived it, which is the §3.6.6 endogeneity arriving through the
    containment.  The issuer's *name* remains matched in any case, so the
    residual is confined to a proposal that names a ticker and never its issuer.
    """

    #: Issuer names and tickers, lower-cased, from the security master and the
    #: discovery markets' listing lists.  Empty means the lookup is unavailable,
    #: which ``entity_mentions`` treats as a refusal to score rather than a pass.
    security_master: frozenset = frozenset()
    #: Ticker symbols, lower-cased, from the same sources.  Kept apart from
    #: ``security_master`` rather than folded into it because the two are matched
    #: by different rules: a name is a word and is matched as a span in any case,
    #: a ticker is a symbol and is matched only in a symbol's shape.
    tickers: frozenset = frozenset()
    #: Rulebook nouns that may head a designator span without a firm being
    #: named.  Consulted by the designator branch alone; see
    #: ``RULEBOOK_STOPWORDS`` for why it is a separate set from the lexicon.
    #: Empty by default, exactly as ``lexicon`` is: an empty set makes the
    #: branch refuse more rather than less, which is the safe direction, and
    #: the seed is supplied by the caller so the value in force is the value
    #: the registration hashed.
    rulebook_stopwords: frozenset = frozenset()
    #: Regulatory and market vocabulary that is *not* an issuer.  Seeded, and
    #: extended by operator mapping in the same idiom as §3.6.5's stream table:
    #: it grows by use rather than by anticipation, and each addition is
    #: recorded.
    lexicon: frozenset = frozenset()

    def mentions(self, text: str) -> List[str]:
        hits: List[str] = []
        for pattern in _IDENTIFIER_PATTERNS:
            hits.extend(m.group(0) for m in pattern.finditer(text))
        for m in _DESIGNATOR_PATTERN.finditer(text):
            phrase = m.group(0)
            lead = phrase.split()[0]
            # Three conditions, and all three must hold.  A designator suffix
            # alone is not enough: it also matched the Rule 16a-8 heading
            # "Trust Holdings and Transactions", which names no firm.
            if not _PROPER_NOUN_LEAD.match(lead):
                continue
            if lead.lower() in self.lexicon:
                continue
            if lead.lower() in self.rulebook_stopwords:
                continue
            hits.append(phrase)
        for m in _BARE_TICKER_PATTERN.finditer(text):
            symbol = m.group(0)
            low = symbol.lower()
            if low in self.lexicon:
                continue
            if low in self.tickers:
                hits.append(symbol)
        # Multi-token names must be matched as spans, not as single tokens.
        # An earlier version tested one capitalised word at a time against the
        # master, which meant "Vodafone Group" could sit in the master and never
        # match anything: the fence's binding layer was inert for every issuer
        # whose name is more than one word, which is most of them.
        for run in re.findall(r"(?:\b[A-Z][\w&.'-]*\b\s*){1,5}", text):
            tokens = run.split()
            for start in range(len(tokens)):
                for end in range(len(tokens), start, -1):
                    span = " ".join(tokens[start:end])
                    low = span.lower().strip(".,;:")
                    if low in self.lexicon:
                        continue
                    if low in self.security_master:
                        hits.append(span)
                        break
        seen, ordered = set(), []
        for h in hits:
            if h not in seen:
                seen.add(h)
                ordered.append(h)
        return ordered

    @staticmethod
    def dates(text: str) -> List[str]:
        """Date shapes, for display beside an entity hit.  Never a hit alone."""

        out: List[str] = []
        for pattern in _DATE_PATTERNS:
            out.extend(m.group(0) for m in pattern.finditer(text))
        return out


#: Seed lexicon: tokens that are entity-shaped and are not entities.
#:
#: **This is the seed, and the registration is the value.**  ``Registration``
#: defaults its ``lexicon`` field to this set and every run reads the
#: registered list, so adding a row here is a re-stamp and a specification
#: version, and the operator-mapped additions are ledgered separately exactly
#: as §3.6.5's stream mappings are.  Until the 27 August re-stamp to
#: `701adbd9d48015ed` the list lived here alone and reached no hash, which
#: meant two runs under one hash could refuse two different sets of tokens; the
#: constant survives as the seed and no longer as the authority.
#:
#: Consulted for two different jobs, which is why both consumers take it as a
#: parameter: the fence ignores what is in it, and the master loader refuses to
#: index it, so a lexicon row changes what the fence CAN SEE as well as what it
#: passes over.
SEED_LEXICON = frozenset(
    w.lower()
    for w in (
        # Venues and market operators
        "ASX", "TSX", "TSXV", "TMX", "LSE", "AIM", "NYSE", "Nasdaq", "Euronext",
        "AEX", "DAX", "CAC", "MDAX", "SDAX", "FTSE", "Russell", "Xetra",
        "Deutsche", "Boerse", "Borse", "Amsterdam", "Paris", "Brussels",
        "Frankfurt", "Prime", "Standard", "SETSqx",
        # Regulators, SROs and standard-setters
        "ASIC", "OSC", "CSA", "CIRO", "IIROC", "ESMA", "BaFin", "AFM", "AMF",
        "FCA", "SEC", "FINRA", "PBAC", "MHRA", "EMA", "FDA", "TGA",
        # Regimes, systems and instruments of law
        "MAR", "MiFID", "UMIR", "SEDI", "SEDAR", "EDGAR", "LINX", "RNS",
        "PDMR", "NCIB", "SOX", "ICB", "GICS", "NI", "RG", "GN", "UK", "US",
        "EU", "EEA", "IPO", "ADV", "ATR", "CEO", "CFO", "NAV", "NII", "FIX",
        "SME", "ETF", "AGM", "TR", "TRS", "CAR", "DTE",
        # Legal-citation and hosting-site vocabulary that collides with real
        # tickers.  Added by operator mapping on the trace of 27 August 2026,
        # which found these five as the whole residue after the ticker rule:
        # CFR and LII are the Code of Federal Regulations and Cornell's Legal
        # Information Institute, ACT is the word in a statute's short title, and
        # III and VII are roman numerals in section and title numbers.  Each is
        # also a listed US ticker, which is why the fence saw them at all.
        "CFR", "LII", "ACT", "III", "VII",
        # Ordinary capitalised prose that is not an entity
        "Appendix", "Article", "Articles", "Regulation", "Directive",
        "Instrument", "Rule", "Rules", "Notice", "Guide", "Guidance",
        "Chapter", "Part", "Form", "Forms", "Section", "Schedule", "Annex",
        "Delegated", "Staff", "Consolidated", "National", "Universal",
        "Market", "Integrity", "Transparency", "Abuse", "Selling", "Short",
        "Listing", "Company", "Manual", "Code", "Practice", "Best",
        "Reporting", "Requirements", "Exemptions", "Insider", "Managers",
        "Substantial", "Holder", "Early", "Warning", "Alternative", "Monthly",
        "Normal", "Course", "Issuer", "Bid", "Automatic", "Securities",
        "Purchase", "Plan", "Pharmaceutical", "Benefits", "Advisory",
        "Committee", "Because", "The", "This", "That", "Once", "Under",
        "Intended", "Clusters", "Movements", "Publication", "Additions",
        "Participants", "Announcement", "Composition", "First", "Managers'",
        "Life", "Scheduled", "Director", "Directors", "Substantial",
        "Interruption", "Aggregated", "Ad", "An", "A", "Where", "Read",
        "Related", "Membership", "Position", "Positions", "Issued",
        "Monthly", "Two", "Three", "Four", "Five", "Ten", "Twelve",
        # Added by operator mapping on the trace of 27 August 2026: the fence
        # refused "Joint and group filings" in Rule 16a-3, The Joint Corp being
        # a listed US issuer whose one-word name is an ordinary English word.
        "Joint",
    )
)

#: Rulebook vocabulary that may lead a **designator span** without the span
#: naming a firm.  Separate from ``SEED_LEXICON`` and consulted by one branch
#: only, because it answers a narrower question: not *is this token an entity*
#: but *may this token head a legal-form span in a rulebook without a firm being
#: named*.  ``Trust Holdings and Transactions`` is the heading of Rule 16a-8,
#: and ``Trust Holdings`` matched the designator grammar exactly as
#: ``Vodafone Group Holdings`` would.
#:
#: **Seeded from evidence, not from anticipation.**  One token, because one is
#: what the 27 August trace over the thirteen US pre-archive documents actually
#: produced: it is the only designator span in the corpus.  It grows by operator
#: mapping in the same idiom as ``SEED_LEXICON`` and §3.6.5's stream table, by
#: use rather than by guesswork, because every speculative row here is a false
#: negative waiting to happen and false negatives are the expensive direction.
#:
#: **The cost, stated.**  A firm whose name *begins* with a stopword loses the
#: designator branch: ``Trust Holdings Inc`` would not be flagged by it.  The
#: name lookup still matches such a firm, and the span matcher is greedy, so
#: ``Northern Trust Holdings`` leads on ``Northern`` and is unaffected.  The
#: residual is confined to a firm whose first word is a rulebook noun and whose
#: name is absent from the security master.
RULEBOOK_STOPWORDS = frozenset({"trust"})

#: Module-level default: lexicon seeded, security master empty.  A caller that
#: has a master supplies one; a caller that does not gets designator and
#: identifier detection only, and the refusal to score that goes with it.
DEFAULT_FENCE = EntityFence(
    lexicon=SEED_LEXICON, rulebook_stopwords=RULEBOOK_STOPWORDS
)


def entity_mentions(text: str, fence: Optional[EntityFence] = None) -> List[str]:
    """Return every entity-shaped token in ``text``.

    An empty list is the only acceptable result for a machine-origin proposal.
    """

    return (fence or DEFAULT_FENCE).mentions(text)


# ---------------------------------------------------------------------------
# Proposal -- the whole of what a discovery agent may emit.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Proposal:
    """A discovery agent's output, and nothing else.

    Note what is *absent*, deliberately, and why each absence is load-bearing:

    * ``evidence_tier`` -- computed from field completeness by §3.6.2, never
      asserted.  An agent that could declare itself quantified would be
      choosing its own screen.
    * ``delta_min`` -- the abandonment threshold.  A pass condition supplied by
      the process that raised the idea returns the threshold to the party that
      wants it cleared.
    * ``stream`` -- for classes outside §3.6.5's table the agent proposes
      nothing, having no authority to invent a stream.
    * ``merit``, ``severity``, ``priority`` -- the table decides.
    * any issuer, instrument or dated episode -- the structural fence.
    """

    #: One sentence, class-level, in the item-extraction idiom.
    event_definition: str
    #: The population the claim is *intended* to hold on.  An intention at this
    #: stage, never a measurement.
    measured_on_intention: str
    #: The class the agent classifies to, or the literal string
    #: ``"unclassified"``.  Classification is the clerk's whole job here.
    event_class: str
    #: Where the agent read the idea.  Must resolve, and must sit in a
    #: partition the agent may read.
    source_ref: str
    source_partition: Partition
    #: Which corpus this was read from.  The exclusivity guarantee is a
    #: property of the corpus, so a directive cannot resolve its scoring_mode
    #: without it.
    corpus_id: str = ""
    #: Free-text mechanism note.  Also entity-fenced.
    mechanism_note: str = ""
    #: Populated only by the control arm, so a drawn mechanism is legible as
    #: drawn rather than proposed.
    drawn_from_grid_cell: Optional[str] = None
    origin: Origin = Origin.AGENT
    raised_at: Optional[datetime] = None

    def fenced_text(self) -> str:
        return " ".join(
            (self.event_definition, self.measured_on_intention, self.mechanism_note)
        )


@dataclass(frozen=True)
class ClaimField:
    """A populated claim with its row-level provenance tag."""

    name: str
    value: str
    provenance: Provenance


# ---------------------------------------------------------------------------
# Intake record -- constructed by the deterministic path.
# ---------------------------------------------------------------------------


@dataclass
class IntakeRecord:
    """A §3.6.2 record.  Constructed, never emitted by an agent."""

    intake_id: str
    origin: Origin
    event_definition: str
    event_class: str
    measured_on: str
    source_ref: str
    source_partition: Partition
    claims: Dict[str, ClaimField] = field(default_factory=dict)
    #: Computed, not asserted.  An intake is quantified only where effect,
    #: horizon and population are all populated and all carry a verified tag.
    evidence_tier: EvidenceTier = EvidenceTier.POINTER
    claimed_effect: Optional[str] = None
    claimed_horizon_sessions: Optional[int] = None
    replication_status: Optional[str] = None
    cost_treatment: Optional[str] = None
    registered_at: Optional[datetime] = None
    scoring_mode: Optional[ScoringMode] = None
    tradable_on: Optional[str] = None

    def compute_evidence_tier(self) -> EvidenceTier:
        verified = {Provenance.VERIFIED_PRIMARY, Provenance.VERIFIED_SECONDARY}
        complete = (
            self.claimed_effect
            and self.claimed_horizon_sessions
            and self.measured_on
            and all(
                self.claims[k].provenance in verified
                for k in ("claimed_effect", "claimed_horizon_sessions", "measured_on")
                if k in self.claims
            )
            and {"claimed_effect", "claimed_horizon_sessions", "measured_on"}
            <= set(self.claims)
        )
        self.evidence_tier = (
            EvidenceTier.QUANTIFIED if complete else EvidenceTier.POINTER
        )
        return self.evidence_tier


# ---------------------------------------------------------------------------
# Directive.
# ---------------------------------------------------------------------------


@dataclass
class PreMortem:
    """P58.  The most plausible false-mechanism explanation, before data."""

    confound: str
    measurable_on_available_data: bool
    author: str
    ratified_by_operator: bool = False
    written_at: Optional[datetime] = None


@dataclass
class SegmentSpan:
    """The sessions and population a directive will consume."""

    start: date
    end: date
    population_key: str

    @property
    def sessions(self) -> int:
        # Trading-session approximation; the production build reads the
        # exchange calendar in the parameter object rather than this ratio.
        return max(0, int((self.end - self.start).days * 252 / 365))

    def overlap_fraction(self, other: "SegmentSpan") -> float:
        """Pairwise overlap, zero where populations do not intersect.

        Two directives measuring disjoint populations over identical dates
        consume different observations and do not overlap; two measuring the
        same population over identical dates overlap completely.
        """

        if self.population_key != other.population_key:
            return 0.0
        lo = max(self.start, other.start)
        hi = min(self.end, other.end)
        if hi <= lo:
            return 0.0
        shared = (hi - lo).days
        smaller = min((self.end - self.start).days, (other.end - other.start).days)
        return shared / smaller if smaller else 0.0


@dataclass
class Directive:
    """A §3.6.8 observation directive."""

    directive_id: str
    intake_id: str
    origin: Origin
    event_class: str
    measured_on: str
    stream: str
    stream_status: StreamStatus
    stream_provenance: StreamProvenance
    scoring_mode: ScoringMode
    span: SegmentSpan
    n_min: int
    #: Registered by the operator, never by the agent.
    delta_min: Optional[float] = None
    delta_units: str = "bps"
    registered_sign: Optional[int] = None
    pre_mortem: Optional[PreMortem] = None
    literature_search_ref: Optional[str] = None
    registered_at: Optional[datetime] = None
    verdict: Optional[Verdict] = None
    observations: int = 0

    @property
    def is_registered(self) -> bool:
        return self.registered_at is not None

    @property
    def may_displace(self) -> bool:
        """Only operator-origin pointers carry displacement rights.

        A scanner producing drafts at volume would otherwise evict the
        operator's own directives simply by out-producing them, which converts
        a capacity rule into a takeover.
        """

        return self.origin is Origin.OPERATOR


# ---------------------------------------------------------------------------
# Items -- surface B.
# ---------------------------------------------------------------------------


@dataclass
class Item:
    """One item arriving from a stream a registered directive names."""

    item_id: str
    source_ref: str
    partition: Partition
    document_type: str = "static"  # static | running
    t_pub_earliest: Optional[datetime] = None
    t_pub_earliest_provenance: Optional[str] = None
    t_pub_observed: Optional[datetime] = None
    t_cat_claimed: Optional[datetime] = None
    t_cat_confirmed: Optional[datetime] = None
    extraction_class: str = "regulatory_filing"
    extracted: Dict[str, object] = field(default_factory=dict)
    issuer: Optional[str] = None
    instrument_referenced: Optional[str] = None
    catalyst_duration_sessions: Optional[int] = None
    ingestion_lag_sessions: Optional[int] = None


@dataclass
class Refusal:
    """Every abort, everywhere, is one of these.

    Carries the code, the fields the §8 template renders from, and the rendered
    summary itself.  Display-only by construction: nothing downstream reads
    ``summary``, so a badly written summary can mislead a reader and cannot
    mislead the system.
    """

    code: str
    subject_id: str
    surface: str
    fields: Dict[str, object] = field(default_factory=dict)
    summary: str = ""
    author: str = "template"
    at: Optional[datetime] = None
