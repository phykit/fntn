"""Market profiles: which venues exist, which are traded, and what that implies.

§13 row 22 made concrete. Each profile records one fact that decides everything
downstream: **is this market inside the traded universe of §0.7(f)?**

* Outside it, discovery and evaluation share no price path, so the corpus
  provides ``cross_market``, at no cost in archive span.
* Inside it, they share one, so ``cross_market`` is unavailable and the corpus
  must provide ``pre_archive`` (material predating the archive's opening
  boundary) or ``forward_only`` (scored only after ``registered_at``).

The distinction is easy to get wrong in exactly one direction: declaring an
in-universe corpus as ``cross_market`` looks harmless, costs nothing, and
silently voids the exclusivity guarantee the whole construction rests on.
``validate_corpus`` refuses it.

**The traded universe is not a setting in this file.** It is §0.7(f), and if it
changes, that is a §0 decision in the specification and this file follows it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .records import ScoringMode


@dataclass(frozen=True)
class MarketProfile:
    code: str
    name: str
    venues: str
    #: True where §0.7(f) admits the venue to the traded universe.
    in_universe: bool
    #: The construction a corpus from this market can provide.
    construction: ScoringMode
    #: Where a complete listed-issuer list comes from, so coverage is a
    #: measurement rather than an estimate (§13 row 25).
    master_source: str
    #: How the master file is loaded.
    master_loader: str
    #: The insider or managers-transaction disclosure this market carries.
    disclosure: str
    notes: str = ""


#: The five markets. `US` and `UK` are the traded universe; the rest are the
#: discovery estate that costs no archive span.
MARKETS: Dict[str, MarketProfile] = {
    "US": MarketProfile(
        code="US",
        name="United States",
        venues="NYSE, Nasdaq",
        in_universe=True,
        construction=ScoringMode.PRE_ARCHIVE,
        master_source="https://www.sec.gov/files/company_tickers.json",
        master_loader="load_sec_tickers",
        disclosure="EDGAR Form 4, filed within two business days of the transaction",
        notes=(
            "In universe, so cross_market is unavailable. The regulator's own "
            "ticker file is the population, which makes coverage complete by "
            "construction. Brochet's post-SOX figures are the live family's "
            "US-measured evidence."
        ),
    ),
    "UK": MarketProfile(
        code="UK",
        name="United Kingdom",
        venues="LSE Main Market, AIM",
        in_universe=True,
        construction=ScoringMode.PRE_ARCHIVE,
        master_source="https://www.londonstockexchange.com/reports?tab=instruments",
        master_loader="load_csv",
        disclosure="RNS PDMR dealing notifications under UK MAR Article 19",
        notes=(
            "In universe, so cross_market is unavailable. This is the market "
            "FGR measured, on 1991-1998 data, which is the strongest figure in "
            "§0.5 and sits three decades before the archive opens."
        ),
    ),
    "AU": MarketProfile(
        code="AU",
        name="Australia",
        venues="ASX",
        in_universe=False,
        construction=ScoringMode.CROSS_MARKET,
        master_source="https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
        master_loader="load_csv",
        disclosure="Appendix 3Y Change of Director's Interest Notice",
        notes=(
            "Outside the universe, so cross_market at no archive cost. The "
            "Appendix 3Y is per-director, timestamped, and carries an explicit "
            "nature-of-change field, which is close in form to RNS PDMR."
        ),
    ),
    "EU": MarketProfile(
        code="EU",
        name="European Union",
        venues="Frankfurt (Prime Standard), Euronext Amsterdam/Paris/Brussels",
        in_universe=False,
        construction=ScoringMode.CROSS_MARKET,
        master_source="Per-venue listed-issuer lists (Deutsche Boerse, Euronext)",
        master_loader="load_csv",
        disclosure="MAR Article 19 managers' transactions; Article 19(11) closed periods",
        notes=(
            "Outside the universe. Richest regime for closed-period and "
            "pledging structure. Listing lists are fragmented across venues, so "
            "coverage must be measured per venue and a combined file leaves it "
            "unknown, which is not readable."
        ),
    ),
    "NZ": MarketProfile(
        code="NZ",
        name="New Zealand",
        venues="NZX Main Board",
        in_universe=False,
        construction=ScoringMode.CROSS_MARKET,
        master_source="https://www.nzx.com/markets/NZSX",
        master_loader="load_csv",
        disclosure="Director and officer disclosure notices under the FMC Act",
        notes=(
            "Outside the universe. Small: a few hundred issuers, so any base "
            "rate drawn from it will be thin and should be treated as "
            "corroborating a mechanism seen elsewhere rather than establishing "
            "one on its own."
        ),
    ),
}


#: Venue names people actually type, mapped to the profile they belong to.
#: Without these a caller writing "ASX" or "EDGAR" gets "not a known market",
#: which is a true statement about the key and a useless one about the world.
ALIASES: Dict[str, str] = {
    "ASX": "AU", "AUS": "AU", "AUSTRALIA": "AU",
    "LSE": "UK", "AIM": "UK", "RNS": "UK", "GB": "UK", "UNITED KINGDOM": "UK",
    "NYSE": "US", "NASDAQ": "US", "SEC": "US", "EDGAR": "US",
    "USA": "US", "UNITED STATES": "US",
    "NZX": "NZ", "NEW ZEALAND": "NZ",
    "EUR": "EU", "EURONEXT": "EU", "FRANKFURT": "EU", "XETRA": "EU",
    "DEUTSCHE BOERSE": "EU", "AMSTERDAM": "EU", "PARIS": "EU",
    "BRUSSELS": "EU", "BAFIN": "EU", "AFM": "EU", "ESMA": "EU",
}


def resolve(market: str) -> Optional[MarketProfile]:
    """Look up by profile code or by a venue name a person would type."""

    key = (market or "").strip().upper()
    return MARKETS.get(key) or MARKETS.get(ALIASES.get(key, ""))


class CorpusInvalid(ValueError):
    pass


def validate_corpus(market: str, declared: ScoringMode | str) -> None:
    """Refuse a corpus whose declared construction its market cannot provide.

    The failure this exists to prevent has one direction: declaring an
    in-universe corpus as ``cross_market``. It costs nothing, looks like a
    configuration detail, and voids the guarantee silently, because nothing
    downstream re-derives it.
    """

    profile = resolve(market)
    if profile is None:
        raise CorpusInvalid(
            f"{market!r} is not a known market or venue. Add a profile rather than "
            "guessing whether it is inside the traded universe: that fact "
            "decides which exclusivity guarantee the corpus can provide."
        )
    mode = ScoringMode(declared) if isinstance(declared, str) else declared
    if not profile.in_universe:
        return  # any construction is available; cross_market is the cheapest
    if mode is ScoringMode.CROSS_MARKET:
        raise CorpusInvalid(
            f"{profile.code} ({profile.venues}) is inside the traded universe of "
            "§0.7(f), so a corpus drawn from it cannot provide cross_market: "
            "discovery and evaluation would share a price path however "
            "different the documents. Use pre_archive (material predating the "
            "archive's opening boundary) or forward_only (scored only after "
            "registered_at)."
        )


def construction_for(market: str) -> ScoringMode:
    profile = resolve(market)
    if profile is None:
        raise CorpusInvalid(f"{market!r} is not a known market or venue")
    return profile.construction


def render() -> str:
    lines = [
        "Market profiles (§13 row 22)",
        "",
        f"{'':<4}{'venues':<52}{'universe':<10}{'construction':<18}",
    ]
    for m in MARKETS.values():
        lines.append(
            f"{m.code:<4}{m.venues[:50]:<52}"
            f"{'traded' if m.in_universe else 'external':<10}"
            f"{m.construction.value:<18}"
        )
    lines += ["", "Master sources:"]
    for m in MARKETS.values():
        lines.append(f"  {m.code}: {m.master_source}  [{m.master_loader}]")
    lines += ["", "Disclosure carried:"]
    for m in MARKETS.values():
        lines.append(f"  {m.code}: {m.disclosure}")
    return "\n".join(lines)
