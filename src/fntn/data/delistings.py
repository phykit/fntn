"""The delisting register: SEC Forms 25, 25-NSE and 15, from EDGAR.

***What this is for, and it is not what it looks like.*** This project cannot
buy survivorship-free prices. **It can obtain, for nothing, a complete list of
what is missing**, and a backtest that knows which names it is missing can
BOUND its own survivorship bias instead of ignoring it.

> **A stated coverage fraction is not a repair. It is the difference between a
> biased number and a biased number that says so.**

**What this is NOT.** It is not a price source, it is not a universe, and it
admits nothing. It cannot make a name tradeable and the funnel does not read it
at decision time. *§0.6 applied explicitly: no gate, no family, no grammar row,
no cost tier, no sizing input, no field read at decision time. It is a ledger
of absence, which `CLAUDE.md` names as procedure.*

**The method it feeds is written down in `docs/DELISTING_REGISTER_2026-08-27.md`
BEFORE any backtest exists**, which is the only moment at which writing it down
costs nothing and proves anything.

---

## The forms, and why two kinds are kept apart

| Form | What it is | Is it a delisting? |
|---|---|---|
| **25** | Notification of removal from listing under Rule 12d2-2, filed by the issuer | ***yes*** |
| **25-NSE** | The same notification filed by the **exchange**, which is how an involuntary removal reaches EDGAR | ***yes, and it is the one that matters***: a company removed against its will is exactly the name a survivorship-biased archive drops |
| **15-12B**, **15-12G**, **15-15D** | Certification of termination of registration, or suspension of the duty to file | ***NO, and conflating them would overstate the missing set*** |
| **15F-12B**, **15F-12G**, **15F-15D** | The foreign-private-issuer variants of the above | ***no***, same reason |

***A Form 15 is deregistration, not delisting.*** It usually follows a
delisting, and it can also be filed by a company that was never listed, or by
one going private, or by one whose holders fell below the statutory threshold.
**Counting Form 15s as delistings would inflate the denominator of the missing
set, which would make the bias bound look tighter than it is.** *A bound that
errs towards comfort is worse than no bound.* They are collected because they
corroborate a Form 25 and because a delisting whose Form 25 is missing may
still show a Form 15, and they are **recorded under their own form code and
never summed with the 25s**.

## What is retained, and what is not

**The register is retained. The quarterly indices are not.** One quarter's
`form.idx` is about 5.5 MB and the span from `archive_opens` runs to fifteen of
them, so retaining the sources would add roughly 80 MB to the tree.

***The cost of not retaining them, stated rather than hidden:*** Class II's
invariant says any input to a decision must be retrievable by commit at the
moment the decision is taken, and **these are not**. What stands in its place
is the fetch log: **URL, retrieval timestamp, byte count and SHA-256 digest of
every index read**, so a later reader can re-fetch and establish byte-identity
or establish that it has changed. *That is weaker than retention and it is
named as weaker. It is not offered as equivalent.*
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ..scanner.trace_filings import (
    ResponseNotTheDocument,
    SEC_HOST,
    TraceCorpusRefused,
    fetch,
    user_agent,
)

#: Where the register lives. **Not under `corpora/`**: a corpus is material a
#: clerk may be shown, and this is not.
REGISTER_ROOT = Path("archive") / "delistings"
REGISTER = REGISTER_ROOT / "register.tsv"
FETCH_LOG = REGISTER_ROOT / "_fetch.tsv"

#: Removal from listing. **These are delistings.**
DELISTING_FORMS: Tuple[str, ...] = ("25", "25-NSE")
#: Deregistration and suspension of the duty to file. **These are NOT
#: delistings** and are never summed with the above. See the module docstring.
DEREGISTRATION_FORMS: Tuple[str, ...] = (
    "15-12B", "15-12G", "15-15D", "15F-12B", "15F-12G", "15F-15D",
)
ALL_FORMS: Tuple[str, ...] = DELISTING_FORMS + DEREGISTRATION_FORMS

MIN_INDEX_BYTES = 100_000
INDEX_MARKER = "Form Type"


def quarterly_index_url(year: int, quarter: int) -> str:
    """EDGAR's quarterly form index: structured, not screen-scraped."""

    if quarter not in (1, 2, 3, 4):
        raise TraceCorpusRefused(
            f"quarter {quarter} does not exist. Refused rather than clamped: a "
            "clamped quarter would silently read a span nobody asked for."
        )
    return f"{SEC_HOST}/Archives/edgar/full-index/{year}/QTR{quarter}/form.idx"


def quarters_between(opens: date, closes: date) -> List[Tuple[int, int]]:
    """Every (year, quarter) the span touches, inclusive at both ends.

    Inclusive because a delisting on the first day of the opening quarter is
    inside the span, and a partial quarter is still a quarter that must be
    read: dropping it would leave a hole in the missing set precisely at the
    boundary, which is where a coverage claim is least defensible.
    """

    if closes < opens:
        raise TraceCorpusRefused(
            f"the span closes ({closes}) before it opens ({opens}). Refused "
            "rather than swapped: a span nobody meant is not repaired by "
            "guessing which end was wrong."
        )
    out: List[Tuple[int, int]] = []
    year, quarter = opens.year, (opens.month - 1) // 3 + 1
    last = (closes.year, (closes.month - 1) // 3 + 1)
    while (year, quarter) <= last:
        out.append((year, quarter))
        quarter += 1
        if quarter == 5:
            year, quarter = year + 1, 1
    return out


@dataclass(frozen=True)
class Event:
    """One filing that removes a name from a listing or a register."""

    form: str
    cik: str
    company: str
    date_filed: str
    path: str

    @property
    def is_delisting(self) -> bool:
        """**Delisting, or merely deregistration.** Never inferred elsewhere."""

        return self.form in DELISTING_FORMS


def parse_index(index_text: str, forms: Iterable[str] = ALL_FORMS) -> List[Event]:
    """Every relevant filing in one quarterly form index.

    A deterministic parser over a field-delimited file, per CLAUDE.md's first
    rule. **The form type is matched EXACTLY**, because `25` is a prefix of
    `25-NSE` and a prefix match would count every exchange notification twice,
    once as itself and once as an issuer filing that never happened.
    """

    wanted = set(forms)
    out: List[Event] = []
    for line in index_text.splitlines():
        parts = line.rsplit(None, 3)
        if len(parts) != 4:
            continue
        head, cik, filed, path = parts
        if not cik.isdigit() or not path.endswith(".txt"):
            continue
        form, _, company = head.partition(" ")
        form = form.strip()
        if form not in wanted:
            continue
        out.append(Event(form, cik, company.strip(), filed, path))
    return out


@dataclass
class Register:
    """The register and the reading it supports. **Counts, never estimates.**"""

    events: List[Event]
    quarters: List[Tuple[int, int]]
    fetch_log: List[Tuple[str, str, int, str]]

    @property
    def delistings(self) -> List[Event]:
        return [e for e in self.events if e.is_delisting]

    @property
    def deregistrations(self) -> List[Event]:
        return [e for e in self.events if not e.is_delisting]

    def by_form(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.events:
            counts[e.form] = counts.get(e.form, 0) + 1
        return counts

    def distinct_delisted_ciks(self) -> int:
        """**Issuers, not filings.** A name can be removed from two listings.

        Reported beside the filing count rather than instead of it, because the
        missing-set denominator the bias bound needs is a count of NAMES and
        the filing count is what the index gives.
        """

        return len({e.cik for e in self.delistings})

    def coverage_fraction(self, names_in_archive: Optional[int]) -> Optional[float]:
        """``N / (N + M)``. **Returns None rather than a number it cannot make.**

        ``N`` is how many names the archive covers and ``M`` is the distinct
        delisted issuers in the span. **With no archive there is no ``N``**, and
        rule 3 says a consuming check refuses to score rather than substituting
        a working value. *A coverage fraction computed against an assumed
        archive size is the exact defect this register exists to prevent,
        wearing the register's own clothes.*
        """

        if names_in_archive is None or names_in_archive <= 0:
            return None
        missing = self.distinct_delisted_ciks()
        return names_in_archive / (names_in_archive + missing)


def build(opens: date, closes: date, pause_s: float = 0.15) -> Register:
    """Read every quarterly index the span touches. One fetch per quarter."""

    import time

    user_agent()  # refuse early, and loudly
    quarters = quarters_between(opens, closes)
    events: List[Event] = []
    log: List[Tuple[str, str, int, str]] = []
    for year, quarter in quarters:
        url = quarterly_index_url(year, quarter)
        body, text = fetch(url, MIN_INDEX_BYTES, INDEX_MARKER)
        log.append((
            url,
            datetime.now(timezone.utc).isoformat(),
            len(body),
            hashlib.sha256(body).hexdigest(),
        ))
        events.extend(parse_index(text))
        time.sleep(pause_s)
    return Register(events=events, quarters=quarters, fetch_log=log)


def write_register(register: Register, root: Path = REGISTER_ROOT) -> Path:
    """The register and its fetch log. Sorted, so the file is diffable."""

    root.mkdir(parents=True, exist_ok=True)
    lines = [
        "# The delisting register. Forms 25 and 25-NSE are DELISTINGS;",
        "# every 15* form is DEREGISTRATION and is never summed with them.",
        "# A Form 15 can be filed by a company that was never listed.",
        f"# quarters read: {len(register.quarters)}, "
        f"{register.quarters[0] if register.quarters else 'n/a'} to "
        f"{register.quarters[-1] if register.quarters else 'n/a'}",
        f"# delisting filings: {len(register.delistings)}; "
        f"distinct delisted issuers: {register.distinct_delisted_ciks()}; "
        f"deregistration filings: {len(register.deregistrations)}",
        "form\tcik\tcompany\tdate_filed\tpath",
    ]
    for e in sorted(register.events, key=lambda e: (e.date_filed, e.form, e.cik)):
        lines.append(f"{e.form}\t{e.cik}\t{e.company}\t{e.date_filed}\t{e.path}")
    out = root / "register.tsv"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    log_lines = [
        "# The sources are NOT retained: fifteen quarterly indices are about",
        "# 80 MB. This log is what makes them re-checkable, and it is WEAKER",
        "# than retention (Class II) and is not offered as equivalent.",
        "url\tretrieved_at\tbytes\tsha256",
    ]
    for row in register.fetch_log:
        log_lines.append("\t".join(str(x) for x in row))
    (root / "_fetch.tsv").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return out
