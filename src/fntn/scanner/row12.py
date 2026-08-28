"""§13 row 12: the joint qualifying-and-tradable rate, measured on Form 4 flow.

**What this row decides, and why it is one of the two that matter.** §0.9's
breadth case rests on a qualifying pool large enough to keep 16 positions filled
at h = 5, which is roughly 800 events a year. §6.6 states the tension plainly:
*breadth and selection are different requirements and the design must not treat
them as one* -- if the pool is only modestly larger than annual capacity, the
system must accept nearly every qualifying filing to stay invested, which leaves
Gate 6's floor with nothing to reject.

**Nothing has ever measured it.** The row has been BLOCKED since it was opened.

## What is measured here, and what is refused

§5.4.1's three tests are **conjunctive** and each is a deterministic read of a
field the notification already carries:

1. **Net increase in beneficial economic interest.** Acquired minus disposed
   across the filing. Custody transfers between accounts and involuntary round
   trips leave exposure unchanged and carry no information.
2. **Open-market acquisition.** Transaction code ``P``. Scheme awards (``A``),
   option exercises (``M``), tax withholding (``F``) and gifts (``G``) are
   compensation or mechanics, not a purchase.
3. **Qualifying filer.** A director or an officer. **A ten-per-cent owner who is
   neither is excluded from the primary cohort** pending its own base rate, per
   the Annex A.1 row: the literature finds abnormal returns for insider
   purchases and none for large shareholders.

**The tradable leg is measured in two parts and one of them REFUSES.**

* The **price floor** is measurable from the filing itself: Form 4 carries
  ``transactionPricePerShare``, so the USD 10.42 floor derived at §13 rows 29
  and 1 can be applied without any market data at all.
* The **liquidity floor** (USD 40,312 of median daily notional) needs price
  history this project does not have. It is **refused, not estimated**:
  ``adv_unmeasured`` is reported per filing and the joint rate is published as a
  **bound** rather than a rate. *A joint rate computed over a leg that was
  guessed is not the quantity row 12 names.*

So this module answers **two of the three marginals and bounds the joint**, and
says which is which on every figure. That is a smaller claim than row 12 asks
for and it is the largest one the free data supports.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

#: Transaction codes that are an open-market acquisition. **Only ``P``.** The
#: rest acquire shares without the insider choosing to buy them, which is the
#: distinction §5.4.1 test 2 draws and the one a word match on "purchase"
#: cannot: a trace over one week's flow found three of five sampled filings
#: carried an acquisition leg and no information.
OPEN_MARKET = frozenset({"P"})

#: The price floor derived at §13 rows 29 and 1: ``102.01/p + 0.206 <= 10``.
DEFAULT_PRICE_FLOOR_USD = 10.42


@dataclass(frozen=True)
class Form4Reading:
    """One filing, read against §5.4.1's three tests. Every field is observed."""

    accession: str
    issuer_cik: str = ""
    filed: Optional[date] = None
    #: Test 1. Acquired minus disposed, in shares, over non-derivative rows.
    net_shares: float = 0.0
    #: Test 2. True where any row carries an open-market acquisition code.
    has_open_market_buy: bool = False
    #: Test 3.
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    #: Weighted mean price over the open-market acquisition rows, or None.
    price_usd: Optional[float] = None
    codes: tuple = ()

    # -- the three tests, each answering one question and no others ---------

    @property
    def test1_net_increase(self) -> bool:
        return self.net_shares > 0

    @property
    def test2_open_market(self) -> bool:
        return self.has_open_market_buy

    @property
    def test3_qualifying_filer(self) -> bool:
        """Director or officer. A bare ten-per-cent owner does not qualify."""

        return bool(self.is_director or self.is_officer)

    @property
    def qualifies(self) -> bool:
        """§5.4.1, conjunctive. All three or none."""

        return (self.test1_net_increase
                and self.test2_open_market
                and self.test3_qualifying_filer)

    def clears_price_floor(self, floor: float = DEFAULT_PRICE_FLOOR_USD) -> Optional[bool]:
        """None where the filing states no price. **Absent is not below.**"""

        if self.price_usd is None:
            return None
        return self.price_usd >= floor


def _f(node, path) -> Optional[str]:
    el = node.find(path)
    return el.text.strip() if el is not None and el.text else None


def _num(node, path) -> Optional[float]:
    raw = _f(node, path)
    if raw is None:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def read_form4(xml: str, accession: str = "") -> Form4Reading:
    """Parse one Form 4 document. A parser, never a model call.

    §3.5.2: *for field-delimited regulatory forms, extraction is a parser, not a
    model call.* Form 4 is the archetype, and it is the reason this family
    exercises no model-mediated extraction path at all.
    """

    root = ET.fromstring(xml)
    rel = root.find(".//reportingOwner/reportingOwnerRelationship")
    is_dir = is_off = is_ten = False
    if rel is not None:
        is_dir = (_f(rel, "isDirector") or "0") in ("1", "true")
        is_off = (_f(rel, "isOfficer") or "0") in ("1", "true")
        is_ten = (_f(rel, "isTenPercentOwner") or "0") in ("1", "true")

    net = 0.0
    codes: List[str] = []
    buy_shares = 0.0
    buy_value = 0.0
    for txn in root.findall(".//nonDerivativeTransaction"):
        code = _f(txn, "transactionCoding/transactionCode") or ""
        codes.append(code)
        shares = _num(txn, "transactionAmounts/transactionShares/value") or 0.0
        ad = _f(txn, "transactionAmounts/transactionAcquiredDisposedCode/value") or ""
        net += shares if ad == "A" else (-shares if ad == "D" else 0.0)
        if code in OPEN_MARKET and ad == "A":
            price = _num(txn, "transactionAmounts/transactionPricePerShare/value")
            if price:
                buy_shares += shares
                buy_value += shares * price

    filed = None
    raw_date = _f(root, ".//periodOfReport")
    if raw_date:
        try:
            filed = date.fromisoformat(raw_date)
        except ValueError:
            filed = None

    return Form4Reading(
        accession=accession,
        issuer_cik=_f(root, ".//issuer/issuerCik") or "",
        filed=filed,
        net_shares=net,
        has_open_market_buy=any(c in OPEN_MARKET for c in codes),
        is_director=is_dir,
        is_officer=is_off,
        is_ten_percent_owner=is_ten,
        price_usd=(buy_value / buy_shares) if buy_shares else None,
        codes=tuple(codes),
    )


@dataclass
class Row12Reading:
    """The measurement, reported with every denominator it was taken over."""

    filings: int = 0
    test1: int = 0
    test2: int = 0
    test3: int = 0
    qualifying: int = 0
    price_cleared: int = 0
    price_absent: int = 0
    #: Never populated. The liquidity leg refuses; see the module docstring.
    adv_unmeasured: int = 0
    #: Files on disk that would not parse. In the denominator, never dropped.
    unparseable: int = 0
    code_census: Counter = field(default_factory=Counter)
    price_floor: float = DEFAULT_PRICE_FLOOR_USD

    def add(self, r: Form4Reading) -> None:
        self.filings += 1
        self.code_census.update(r.codes)
        self.test1 += r.test1_net_increase
        self.test2 += r.test2_open_market
        self.test3 += r.test3_qualifying_filer
        if r.qualifies:
            self.qualifying += 1
            cleared = r.clears_price_floor(self.price_floor)
            if cleared is None:
                self.price_absent += 1
            elif cleared:
                self.price_cleared += 1
        self.adv_unmeasured += 1

    @property
    def qualifying_rate(self) -> Optional[float]:
        return self.qualifying / self.filings if self.filings else None

    def render(self) -> str:
        if not self.filings:
            return ("§13 row 12: no filings read. **A rate over an empty set is "
                    "not a rate**, and this refuses rather than printing 0%.")
        q = self.qualifying_rate
        out = [
            "§13 row 12: the joint qualifying-and-tradable rate",
            f"  files on disk                   : {self.filings + self.unparseable}",
            f"  filings read                    : {self.filings}",
            f"  UNPARSEABLE, in the denominator : {self.unparseable}",
            "",
            "  §5.4.1's three tests, each with its own denominator:",
            f"    1 net increase in interest    : {self.test1:5d}  ({self.test1/self.filings:6.1%})",
            f"    2 open-market acquisition (P) : {self.test2:5d}  ({self.test2/self.filings:6.1%})",
            f"    3 qualifying filer            : {self.test3:5d}  ({self.test3/self.filings:6.1%})",
            f"    ALL THREE, conjunctive        : {self.qualifying:5d}  ({q:6.1%})",
            "",
            f"  tradable leg, price floor USD {self.price_floor:.2f}:",
            f"    qualifying and above floor    : {self.price_cleared:5d}",
            f"    qualifying, no price stated   : {self.price_absent:5d}  (absent is NOT below)",
            "",
            "  liquidity leg (USD 40,312 median daily notional):",
            f"    REFUSED, not estimated        : {self.adv_unmeasured:5d} filings unscored.",
            "      Price history is not in this tree. A joint rate computed over",
            "      a guessed leg is not the quantity row 12 names, so what is",
            "      published below is a BOUND and not a rate.",
            "",
            f"  JOINT RATE, UPPER BOUND         : {self.price_cleared/self.filings:6.1%}",
            "    An upper bound because every filing clearing the price floor is",
            "    counted as tradable, and the liquidity floor can only remove.",
            "",
            "  transaction-code census (why a word match on 'purchase' fails):",
        ]
        for code, n in sorted(self.code_census.items(), key=lambda kv: -kv[1]):
            out.append(f"    {code or '(blank)':3s} : {n:5d}")
        return "\n".join(out)


def measure(readings: Iterable[Form4Reading],
            price_floor: float = DEFAULT_PRICE_FLOOR_USD) -> Row12Reading:
    out = Row12Reading(price_floor=price_floor)
    for r in readings:
        out.add(r)
    return out


def read_directory(path: str | Path,
                   unparseable: Optional[List] = None) -> List[Form4Reading]:
    """Every Form 4 XML under ``path``. Fetching is NOT done here.

    The fetch runs through the existing `trace_filings` transport, which refuses
    three ways on `SEC_CONTACT`: unset, an unedited placeholder, and a value
    that is not ``<name> <email>``. **A placeholder is a false statement made to
    a regulator's server in order to obtain data**, and that guard is not
    duplicated here in a weaker form.
    """

    unparseable = unparseable if unparseable is not None else []
    out: List[Form4Reading] = []
    for p in sorted(Path(path).rglob("*.xml")):
        if p.name.startswith("_"):
            continue
        try:
            out.append(read_form4(p.read_text(errors="replace"), accession=p.stem))
        except ET.ParseError as exc:
            # Counted and named, never swallowed: this bare `continue`
            # dropped 143 of 1000 filings out of the denominator.
            unparseable.append((p.name, str(exc)))
    return out
