"""The security master: the entity fence's binding layer, and §13 row 25.

The fence detects an episode-level proposal by looking a token up in a closed
list, not by matching a pattern over an open vocabulary. That design is only as
good as the list, which makes coverage a measured quantity rather than an
assumption: **an issuer absent from the master is an episode the fence cannot
see**, and it will pass silently.

So the master reports its coverage per market, and a market below the registered
floor is **not readable for discovery**. That is the same refusal as everywhere
else in this system: an input whose completeness is unknown does not get used at
whatever completeness it happens to have.

Input format: CSV with a header, and at minimum a name column. Ticker and market
columns are used where present. Column names are matched case-insensitively
against a small set of aliases, because listing files from different exchanges
disagree about what to call the same field and normalising them by hand is the
kind of chore that gets skipped.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .records import SEED_LEXICON, RULEBOOK_STOPWORDS, EntityFence

_NAME_COLUMNS = ("name", "company", "company name", "issuer", "security name",
                 "companyname", "issuer name", "long name", "description")
_TICKER_COLUMNS = ("ticker", "symbol", "code", "asx code", "tidm", "epic",
                   "root symbol", "trading symbol", "instrument")
_MARKET_COLUMNS = ("market", "exchange", "listing market", "venue", "segment")

#: **Legal-form** suffixes only, stripped when indexing, so that
#: "Acme Holdings plc" also matches a proposal saying "Acme Holdings".
#:
#: "Holdings", "Group" and "Company" are deliberately NOT here. They are name
#: components rather than legal forms, and stripping them reduces
#: "Acme Holdings plc" to "acme", which is short, generic, and would refuse
#: every proposal containing the word. The first version of this regex did
#: exactly that, and the test caught it.
_SUFFIX = re.compile(
    r"(?:\s+(?:plc|inc\.?|ltd\.?|limited|corp\.?|corporation|"
    r"n\.?v\.?|s\.?a\.?|ag|gmbh|se|ab|asa|nv|sa))+\s*$",
    re.I,
)

#: Names too short or too generic to index. A one-token name that collides with
#: ordinary prose would refuse every proposal containing that word.
_MIN_NAME_LEN = 4


@dataclass
class MasterCoverage:
    """§13 row 25, per market."""

    market: str
    rows: int
    indexed_names: int
    indexed_tickers: int
    skipped_generic: int = 0
    #: Population the market is being measured against, where the operator can
    #: supply one. `None` means coverage is unknown, which is not the same as
    #: complete, and the renderer says so.
    listed_total: Optional[int] = None

    @property
    def coverage(self) -> Optional[float]:
        if not self.listed_total:
            return None
        return min(1.0, self.rows / self.listed_total)


@dataclass
class SecurityMaster:
    names: Set[str] = field(default_factory=set)
    tickers: Set[str] = field(default_factory=set)
    per_market: Dict[str, MasterCoverage] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    #: The lexicon the loader filters against, which is a different job from
    #: the one the fence's copy does and has to be the same list. A token here
    #: never enters the master at all, so a lexicon row changes what the fence
    #: **can see** as well as what it ignores. Defaults to the module seed so a
    #: bare ``SecurityMaster()`` still filters; the CLI passes the registered
    #: list, so a run's master is attributable to the run's hash.
    lexicon: frozenset = SEED_LEXICON

    # -- loading -----------------------------------------------------------

    @staticmethod
    def _pick(header: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
        lowered = {h.strip().lower(): h for h in header}
        for c in candidates:
            if c in lowered:
                return lowered[c]
        for key, original in lowered.items():
            if any(c in key for c in candidates):
                return original
        return None

    def load_csv(
        self,
        path: str | Path,
        market: Optional[str] = None,
        listed_total: Optional[int] = None,
    ) -> MasterCoverage:
        p = Path(path)
        with p.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            name_col = self._pick(header, _NAME_COLUMNS)
            tick_col = self._pick(header, _TICKER_COLUMNS)
            mkt_col = self._pick(header, _MARKET_COLUMNS)
            if not name_col and not tick_col:
                raise ValueError(
                    f"{p}: no name or ticker column found in header {header!r}. "
                    "The fence cannot be built from a file it cannot read, and "
                    "guessing a column would put an unverified list behind a "
                    "binding check."
                )
            # One CSV may carry several markets. Group by them rather than
            # collapsing to whichever appeared last, which is what an earlier
            # version did: it reported one market as covering every row and the
            # others as absent, which is worse than no coverage figure at all
            # because it looks like a measurement.
            default_market = market or p.stem
            buckets: Dict[str, MasterCoverage] = {}

            def bucket(name: str) -> MasterCoverage:
                if name not in buckets:
                    buckets[name] = MasterCoverage(
                        market=name, rows=0, indexed_names=0, indexed_tickers=0,
                        # A per-market total cannot be inferred from a combined
                        # file, so it is only attached where the caller named a
                        # single market.
                        listed_total=listed_total if market else None,
                    )
                return buckets[name]

            for row in reader:
                row_market = default_market
                if mkt_col and not market:
                    row_market = (row.get(mkt_col) or "").strip() or default_market
                cov = bucket(row_market)
                cov.rows += 1
                if name_col:
                    for variant in self._name_variants(row.get(name_col, "")):
                        if len(variant) < _MIN_NAME_LEN:
                            cov.skipped_generic += 1
                            continue
                        if variant in self.lexicon:
                            cov.skipped_generic += 1
                            continue
                        self.names.add(variant)
                        cov.indexed_names += 1
                if tick_col:
                    t = (row.get(tick_col) or "").strip().lower()
                    if t and t not in self.lexicon:
                        self.tickers.add(t)
                        cov.indexed_tickers += 1
        for name, cov in buckets.items():
            existing = self.per_market.get(name)
            if existing is None:
                self.per_market[name] = cov
            else:
                existing.rows += cov.rows
                existing.indexed_names += cov.indexed_names
                existing.indexed_tickers += cov.indexed_tickers
                existing.skipped_generic += cov.skipped_generic
                if cov.listed_total is not None:
                    existing.listed_total = cov.listed_total
        self.sources.append(str(p))
        if len(buckets) == 1:
            return next(iter(buckets.values()))
        return MasterCoverage(
            market=f"{len(buckets)} markets",
            rows=sum(c.rows for c in buckets.values()),
            indexed_names=sum(c.indexed_names for c in buckets.values()),
            indexed_tickers=sum(c.indexed_tickers for c in buckets.values()),
            skipped_generic=sum(c.skipped_generic for c in buckets.values()),
        )

    def load_sec_tickers(
        self, path: str | Path, market: str = "US", listed_total: Optional[int] = None
    ) -> MasterCoverage:
        """Load the SEC's own `company_tickers.json`.

        The authoritative, free, complete list of every issuer with an EDGAR
        filing obligation, published by the regulator whose filings the agent
        would be reading. Using it means `listed_total` is the file's own row
        count, so US coverage is 100% by construction rather than by estimate:
        the master and the population are the same object.

            https://www.sec.gov/files/company_tickers.json

        Shape: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
        """

        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = raw.values() if isinstance(raw, dict) else raw
        cov = MasterCoverage(
            market=market, rows=0, indexed_names=0, indexed_tickers=0,
            listed_total=listed_total,
        )
        for row in rows:
            cov.rows += 1
            for variant in self._name_variants(str(row.get("title", ""))):
                if len(variant) < _MIN_NAME_LEN or variant in self.lexicon:
                    cov.skipped_generic += 1
                    continue
                self.names.add(variant)
                cov.indexed_names += 1
            t = str(row.get("ticker", "")).strip().lower()
            if t and t not in self.lexicon:
                self.tickers.add(t)
                cov.indexed_tickers += 1
        # The file is the population, so coverage is complete unless the caller
        # deliberately measures against a different denominator.
        if cov.listed_total is None:
            cov.listed_total = cov.rows
        existing = self.per_market.get(market)
        if existing is None:
            self.per_market[market] = cov
        else:
            existing.rows += cov.rows
            existing.indexed_names += cov.indexed_names
            existing.indexed_tickers += cov.indexed_tickers
            existing.listed_total = (existing.listed_total or 0) + cov.rows
        self.sources.append(str(path))
        return cov

    @staticmethod
    def _name_variants(raw: str) -> List[str]:
        base = (raw or "").strip().lower()
        if not base:
            return []
        stripped = _SUFFIX.sub("", base).strip()
        out = {base}
        if stripped and stripped != base:
            out.add(stripped)
        return [v for v in out if v]

    # -- use ---------------------------------------------------------------

    def as_fence(
        self, lexicon=None, stopwords=RULEBOOK_STOPWORDS
    ) -> EntityFence:
        """Names and tickers go in separately, and the fence matches them apart.

        An earlier version passed the union as one lookup set. That put 10,359
        unfiltered US tickers, 7,268 of them four characters or fewer, into the
        same set as the issuer names, where the fence's span matcher tried them
        against every capitalised word in the text. ``Note``, ``Are``, ``For``
        and the single letters are all tickers, so ordinary English refused. The
        two are separated here because they are matched by different rules; see
        ``EntityFence`` for the rule and for the false negative it accepts.
        """

        return EntityFence(
            security_master=frozenset(self.names),
            tickers=frozenset(self.tickers),
            #: Defaults to the list this master was loaded under rather than to
            #: the module seed. The loader and the fence consult the lexicon for
            #: different purposes and a fence built from a master filtered by a
            #: different list would refuse a set neither list explains.
            lexicon=frozenset(self.lexicon if lexicon is None else lexicon),
            rulebook_stopwords=frozenset(stopwords),
        )

    def readable_markets(self, floor: float) -> List[str]:
        """Markets whose coverage clears the floor.

        A market with unknown coverage does **not** clear it. Unknown is not a
        synonym for complete, and treating it as one is how a fence acquires a
        hole nobody can point at.
        """

        out = []
        for m, cov in self.per_market.items():
            if cov.coverage is not None and cov.coverage >= floor:
                out.append(m)
        return out

    def unreadable_markets(self, floor: float) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for m, cov in self.per_market.items():
            if cov.coverage is None:
                out[m] = (
                    f"coverage unknown: no listed_total supplied for {cov.rows} "
                    "rows, so the share of the market present in the master "
                    "cannot be computed"
                )
            elif cov.coverage < floor:
                out[m] = (
                    f"coverage {cov.coverage:.1%} below floor {floor:.0%} "
                    f"({cov.rows} of {cov.listed_total})"
                )
        return out

    def render(self, floor: Optional[float] = None) -> str:
        lines = [
            "Security master (§13 row 25)",
            f"  sources                      : {len(self.sources)}",
            f"  indexed names                : {len(self.names)}",
            f"  indexed tickers              : {len(self.tickers)}",
        ]
        for m, cov in sorted(self.per_market.items()):
            c = f"{cov.coverage:.1%}" if cov.coverage is not None else "unknown"
            lines.append(
                f"    {m:<24} rows={cov.rows:<6} coverage={c:<8} "
                f"skipped_generic={cov.skipped_generic}"
            )
        if floor is not None:
            bad = self.unreadable_markets(floor)
            if bad:
                lines.append("  NOT READABLE for discovery:")
                for m, why in bad.items():
                    lines.append(f"    {m}: {why}")
            else:
                lines.append(f"  every market clears the {floor:.0%} coverage floor")
        return "\n".join(lines)
