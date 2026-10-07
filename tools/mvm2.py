#!/usr/bin/env python3
"""
mvm2.py - the amended kill test for the insider-purchase family.

NON-EVIDENTIARY, exactly as tools/mvm.py is. It may not be cited as a
calibration, registers no parameter, and no §13 row may take a reading from it.

It amends the protocol tools/mvm.py fixed on 19 September 2026. The amendment
is docs/MVM_AMENDMENT_2026-10-07.md and was fixed on 7 October 2026, BEFORE any
price was fetched and before any result existed. tools/mvm.py is left untouched
(rule 4: nothing is overwritten); its PROTOCOL is imported here, so every
constant the two share has one copy.

Why an amendment was needed, in one line each (the document has the argument):
  A1  the registered statistic is a RAW return, so a rising market passes it
      with no edge at all; the decision statistic here is benchmark-adjusted.
  A2  form.idx lists a filing once per filer, so the registered harness would
      have counted each purchase two or more times; events here are one per
      issuer per filing date, and one open position per issuer.
  A3  a flat 15.7 bp is the cost of the MOST liquid bucket only; costs here are
      also charged from the project's own registered table, by liquidity bucket.
  A4  the event population comes from the SEC's quarterly Insider Transactions
      Data Sets (about fifteen downloads) and not from about a million filings.
  A5  the price floor is read from the filing, liquidity is trailing and not
      whole-span, prices are total-return, and identity is checked.
  A6  a free price source omits delisted names, so it can kill and cannot pass.

Usage:
    export SEC_CONTACT="Your Name your@email.com"
    python3 tools/mvm2.py --provider yahoo --smoke 150 --out out/   # coverage only
    python3 tools/mvm2.py --provider yahoo --out out/
    python3 tools/mvm2.py --provider eodhd --out out/               # needs EODHD_KEY
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import io
import json
import math
import os
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Iterable, Sequence

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mvm  # noqa: E402  (the 19 September protocol; imported, never edited)

BASE = mvm.PROTOCOL

# ----------------------------------------------------------------------------
# THE AMENDMENT. Fixed 2026-10-07, before any price was fetched.
# Do not edit after a result exists. Its hash is printed on every output.
# ----------------------------------------------------------------------------

PROTOCOL2 = {
    "amends": "tools/mvm.py PROTOCOL, registered 2026-09-19",
    "amended_on": "2026-10-07",
    "unchanged": {
        "span_start": BASE["span_start"],
        "span_end": BASE["span_end"],
        "horizon_sessions": BASE["horizon_sessions"],
        "min_share_price_usd": BASE["min_share_price_usd"],
        "min_median_notional_usd": BASE["min_median_notional_usd"],
        "flat_round_trip_cost_bps": BASE["round_trip_cost_bps"],
        "event": "Form 4 (never 4/A), non-derivative table, transaction code P, "
                 "acquired, by a filer who is an officer or a director",
        "entry": "open of the first session strictly after the filing date",
        "exit": "open, h sessions after entry",
        "gates": "none",
    },
    "A1_benchmarks": ["SPY", "IWM"],
    "A1_statistic": "abnormal return = trade open-to-open total return minus "
                    "the benchmark's over the same two opens; the reading is "
                    "the LOWER of the two benchmarks' lower 95% bounds",
    "A2_event_unit": "one event per (issuer CIK, filing date)",
    "A2_one_position_per_issuer": True,
    "A2_interval": "two-sided 95%, clustered by calendar month of entry, "
                   "Student t on (clusters - 1) degrees of freedom; fewer than "
                   "10 clusters is refused, not approximated",
    "A3_cost_tiers_bps": [
        # (label, lower bound of trailing median daily notional USD, midpoint, conservative)
        ["B1 >$1bn", 1e9, 15.7, 18.7],
        ["B2 $100m-$1bn", 1e8, 28.7, 38.7],
        ["B3 $10m-$100m", 1e7, 78.7, 108.7],
        ["B4 $1m-$10m", 1e6, 208.7, 308.7],
    ],
    "A3_cost_source": "docs/ROW29_REDERIVED_2026-08-27.md, the recomputation of "
                      "spec §5.2.2 at row 29's 8.7 bp bound. Below USD 1m a day "
                      "the table has no row: bucket B5 takes the flat cost only "
                      "and is refused by every tiered statistic",
    "A4_event_source": "SEC Insider Transactions Data Sets, quarterly",
    "A5_price_floor_on": "the filing's own volume-weighted purchase price "
                         "(§13 row 12's precedent)",
    "A5_liquidity_window_sessions": 63,
    "A5_liquidity_min_sessions": 21,
    "A5_identity_ratio": [0.5, 2.0],
    "A5_identity_note": "filing purchase price over the provider's nominal "
                        "close on the last transaction date; outside the band "
                        "the ticker is not the security the insider bought",
    "A5_prices": "open, adjusted for splits and dividends",
    "A6_survivorship": "a provider that omits delisted names licenses KILL and "
                       "licenses nothing above it; any other branch is "
                       "PROVISIONAL until re-run on an archive that keeps them",
    "A6_kill_stands_if_unpriced_would_need_bps": 230.0,
    "A6_kill_note": "on a provider that omits delisted names a KILL is final "
                    "only if the unpriced events would have needed to average "
                    "more than 230 bp, the largest US effect this project has "
                    "ever documented for the family (spec §0.5), to bring L(G) "
                    "to zero; otherwise it too is PROVISIONAL",
    "A6_pass_note": "on any provider, a branch above KILL is PROVISIONAL unless "
                    "its bound survives charging every event lost on a delisted "
                    "issuer a total loss",
    "tail_rule_abs_gross_pct": 100.0,
    "T_populations": {"B1-B4": ["B1", "B2", "B3", "B4"], "B1-B2": ["B1", "B2"]},
    "T_note": "two pre-declared populations, so two looks; clearing on either "
              "counts and the verdict names which",
    "time_cost_gbp": 15000.0,
    "slot_notional_gbp": 6250.0,
    "trades_per_year_at_full_book": 806.4,
    "time_hurdle_bps_at_full_book": 29.8,
    "time_hurdle_derivation": "(22,000 - 7,000) / 504 at a full book: "
                              "programme_hurdle's tracker-plus-time rung less its "
                              "tracker rung, the tracker being removed by A1. A "
                              "population supplying fewer than 806 trades a year "
                              "cannot keep sixteen slots filled, so its hurdle is "
                              "15,000 / (trades a year x 0.625) and is higher",
    "decision_rule": (
        "Fixed before the result. Abnormal returns throughout; every bound is "
        "the lower of the SPY and IWM readings.\n"
        "  G = all trades, flat 15.7 bp: the most generous reading available.\n"
        "  T = buckets B1 to B4, and separately B1 to B2, each trade at its "
        "bucket's registered midpoint cost.\n"
        "  KILL             L(G) <= 0. No edge over a tracker at the cheapest "
        "cost this project has ever registered.\n"
        "  COST-DETERMINED  L(G) > 0 and L(T) <= 0 on both populations. A gross "
        "effect exists; whether it pays turns on spreads nobody has measured "
        "(§13 row 36). Not a pass and no capital.\n"
        "  BEATS A TRACKER  L(T) > 0 on a population, under that population's "
        "time hurdle. Does not pay for the time.\n"
        "  PAYS FOR ITSELF  L(T) >= the time hurdle on a population: 29.8 bp at "
        "806 trades a year, more where the population supplies fewer.\n"
        "  TAIL RULE        the branch is recomputed without trades whose gross "
        "five-session return exceeds 100% in absolute value; if the branch "
        "differs, the LOWER branch is the verdict and it is marked "
        "TAIL-DEPENDENT."
    ),
    "smoke_seed": 20261007,
}


def protocol_hash() -> str:
    blob = json.dumps({"base": BASE, "amendment": PROTOCOL2}, sort_keys=True,
                      separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


STAMP = "NON-EVIDENTIARY. May not be cited as a calibration."
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SEC_BASES = (
    "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/",
    "https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/",
)


def notice(title: str, payload) -> None:
    """One line a GitHub Actions run records as an annotation. Outside Actions
    it prints nothing."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    msg = payload if isinstance(payload, str) else json.dumps(payload, separators=(",", ":"), default=str)
    msg = msg.replace("%", "%25").replace("\r", " ").replace("\n", "%0A")
    print(f"::notice title={title}::{msg[:3800]}", flush=True)


class Refusal(SystemExit):
    """A named refusal. Rule 3: a missing input stops the run; it is never
    replaced by a working value."""


def refuse(code: str, why: str) -> "Refusal":
    return Refusal(f"REFUSED [{code}]: {why}")


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

def sec_contact() -> str:
    c = os.environ.get("SEC_CONTACT", "").strip()
    low = c.lower()
    if not c or "your name" in low or "example." in low or "@" not in c:
        raise refuse("sec_contact_absent",
                     "SEC_CONTACT must be a real '<name> <email>'. A placeholder "
                     "is a false statement to a regulator's server.")
    return c


class Transient(Exception):
    pass


def http_get(url: str, ua: str, *, tries: int = 5, timeout: int = 90,
             pause: float = 0.0) -> tuple[int, bytes]:
    """-> (status, body). 404 is an answer and is returned. 429 and 5xx are
    retried and then raised as Transient: an unanswered question is never read
    as 'no data'."""
    last: object = None
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": ua, "Accept-Encoding": "gzip", "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if "gzip" in (r.headers.get("Content-Encoding") or ""):
                    import gzip
                    raw = gzip.decompress(raw)
                if pause:
                    time.sleep(pause)
                return r.status, raw
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                body = b""
                try:
                    body = e.read()
                except Exception:               # noqa: BLE001
                    pass
                if pause:
                    time.sleep(pause)
                return e.code, body
            last = f"HTTP {e.code}"
        except Exception as e:                  # noqa: BLE001
            last = e
        if attempt + 1 < tries:
            time.sleep(min(60.0, 2.0 * (2 ** attempt)))
    raise Transient(f"{url.split('?')[0]}: {last}")


# ----------------------------------------------------------------------------
# Step 1. The event population (A4)
# ----------------------------------------------------------------------------

def quarters(start: dt.date, end: dt.date) -> list[str]:
    out, y, q = [], start.year, (start.month - 1) // 3 + 1
    while (y, q) <= (end.year, (end.month - 1) // 3 + 1):
        out.append(f"{y}q{q}")
        q += 1
        if q == 5:
            y, q = y + 1, 1
    return out


def fetch_datasets(start: dt.date, end: dt.date, cache: pathlib.Path) -> tuple[list[pathlib.Path], list[dict]]:
    """Every quarterly archive in the span. A missing quarter at the END of the
    span shortens the span and says so; a missing quarter inside it refuses."""
    cache.mkdir(parents=True, exist_ok=True)
    ua = sec_contact()
    qs = quarters(start, end)
    got: list[pathlib.Path] = []
    manifest: list[dict] = []
    missing: list[str] = []
    for q in qs:
        f = cache / f"{q}_form345.zip"
        src = "cache"
        if not (f.exists() and zipfile.is_zipfile(f)):
            src = ""
            for base in SEC_BASES:
                url = f"{base}{q}_form345.zip"
                status, body = http_get(url, ua, pause=0.5)
                if status == 200 and body[:2] == b"PK":
                    f.write_bytes(body)
                    src = url
                    break
            if not src:
                missing.append(q)
                print(f"  {q}: not published at either SEC path", flush=True)
                continue
        manifest.append({"quarter": q, "bytes": f.stat().st_size, "source": src,
                         "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
        got.append(f)
        print(f"  {q}: {f.stat().st_size:,} bytes ({'cached' if src == 'cache' else 'fetched'})",
              flush=True)
    if not got:
        raise refuse("event_archive_absent", "no quarterly archive could be fetched")
    return got, manifest


def _member(z: zipfile.ZipFile, name: str) -> str:
    for n in z.namelist():
        if n.upper().rsplit("/", 1)[-1] == name.upper():
            return n
    raise refuse("event_archive_schema", f"{name} is not in {z.filename}")


def _rows(z: zipfile.ZipFile, name: str, need: Sequence[str], funnel: dict) -> Iterable[dict]:
    """Rows of one table. A row with too few or too many fields has had a tab or
    a newline typed into free text, so its columns cannot be trusted: it is
    counted and skipped, never read."""
    with z.open(_member(z, name)) as fh:
        rd = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", errors="replace", newline=""),
                            delimiter="\t", quoting=csv.QUOTE_NONE)
        absent = [c for c in need if c not in (rd.fieldnames or [])]
        if absent:
            raise refuse("event_archive_schema",
                         f"{name} in {z.filename} lacks {absent}; has {rd.fieldnames}")
        for r in rd:
            if None in r or any(r[c] is None for c in need):
                funnel["malformed_rows"] += 1
                continue
            yield r


def parse_sec_date(s: str) -> dt.date | None:
    s = (s or "").strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s.title() if fmt == "%d-%b-%Y" else s, fmt).date()
        except ValueError:
            continue
    return None


_EXCH = re.compile(r"^(NYSE(\s*AMERICAN|\s*ARCA|\s*MKT)?|NASDAQ(GS|GM|CM)?|AMEX|OTC(QB|QX)?|OTC\s*PINK)\s*[:\-]\s*", re.I)
_PLAIN = re.compile(r"^[A-Z]{1,5}$")
_CLASS = re.compile(r"^([A-Z]{1,5})[.\-/ ]([A-Z])$")


def norm_ticker(raw: str) -> str | None:
    """Canonical form 'ABC' or 'ABC.B'. Anything else is refused, not guessed:
    a symbol field naming two securities, or none, names no tradable one."""
    s = (raw or "").strip().upper().strip("()[]\"'")
    s = _EXCH.sub("", s).strip()
    if s in {"NONE", "NA", "NULL", "N/A", "N.A", "N-A"}:
        return None                              # a blank written out, not a symbol
    if _PLAIN.match(s):
        return s
    m = _CLASS.match(s)
    return f"{m.group(1)}.{m.group(2)}" if m else None


def _num(s: str) -> float:
    try:
        return float((s or "").strip())
    except ValueError:
        return 0.0


@dataclasses.dataclass
class Event:
    cik: str
    ticker: str
    filed: dt.date
    shares: float
    notional: float
    last_trans: dt.date | None
    n_accessions: int

    @property
    def vwap(self) -> float:
        return self.notional / self.shares if self.shares else 0.0


def parse_archive(path: pathlib.Path, funnel: dict) -> list[dict]:
    """Accession-level purchase records from one quarterly archive."""
    out: list[dict] = []
    with zipfile.ZipFile(path) as z:
        sub: dict[str, tuple[str, str, dt.date]] = {}
        for r in _rows(z, "SUBMISSION.tsv", ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE",
                                             "ISSUERCIK", "ISSUERTRADINGSYMBOL"], funnel):
            funnel["submissions"] += 1
            if r["DOCUMENT_TYPE"].strip().upper() != "4":
                continue
            funnel["form4"] += 1
            d = parse_sec_date(r["FILING_DATE"])
            if d is None:
                funnel["bad_filing_date"] += 1
                continue
            sub[r["ACCESSION_NUMBER"]] = (r["ISSUERCIK"].strip().lstrip("0"),
                                          r["ISSUERTRADINGSYMBOL"], d)
        role: set[str] = set()
        for r in _rows(z, "REPORTINGOWNER.tsv", ["ACCESSION_NUMBER", "RPTOWNER_RELATIONSHIP"], funnel):
            rel = r["RPTOWNER_RELATIONSHIP"].upper()
            if "DIRECTOR" in rel or "OFFICER" in rel:
                role.add(r["ACCESSION_NUMBER"])
        agg: dict[str, list] = {}
        for r in _rows(z, "NONDERIV_TRANS.tsv", ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE",
                                                 "TRANS_SHARES", "TRANS_PRICEPERSHARE",
                                                 "TRANS_ACQUIRED_DISP_CD"], funnel):
            acc = r["ACCESSION_NUMBER"]
            if acc not in sub:
                continue
            if r["TRANS_CODE"].strip().upper() != "P":
                continue
            funnel["p_rows"] += 1
            if r["TRANS_ACQUIRED_DISP_CD"].strip().upper() != "A":
                continue
            sh, px = _num(r["TRANS_SHARES"]), _num(r["TRANS_PRICEPERSHARE"])
            if sh <= 0 or px <= 0:
                funnel["p_rows_no_price_or_shares"] += 1
                continue
            a = agg.setdefault(acc, [0.0, 0.0, None])
            a[0] += sh
            a[1] += sh * px
            td = parse_sec_date(r["TRANS_DATE"])
            if td and (a[2] is None or td > a[2]):
                a[2] = td
        for acc, (sh, notional, td) in agg.items():
            funnel["purchase_accessions"] += 1
            if acc not in role:
                funnel["not_officer_or_director"] += 1
                continue
            cik, sym, d = sub[acc]
            out.append({"acc": acc, "cik": cik, "sym": sym, "filed": d,
                        "shares": sh, "notional": notional, "last_trans": td})
    return out


def build_events(records: Sequence[dict], start: dt.date, end: dt.date, funnel: dict) -> list[Event]:
    """A2: one event per (issuer, filing date). The price floor is applied here,
    on the filing's own price, so that no price series is fetched to apply it."""
    minpx = BASE["min_share_price_usd"]
    seen: set[str] = set()
    groups: dict[tuple[str, dt.date], list[dict]] = {}
    for r in records:
        if r["acc"] in seen:
            funnel["duplicate_accession"] += 1
            continue
        seen.add(r["acc"])
        if not (start <= r["filed"] <= end):
            funnel["outside_span"] += 1
            continue
        groups.setdefault((r["cik"], r["filed"]), []).append(r)
    events: list[Event] = []
    for (cik, filed), rs in sorted(groups.items()):
        funnel["issuer_days"] += 1
        syms = [t for t in (norm_ticker(r["sym"]) for r in rs) if t]
        if not syms or not cik:
            funnel["bad_ticker"] += 1
            continue
        ticker = max(sorted(set(syms)), key=syms.count)
        sh = sum(r["shares"] for r in rs)
        notional = sum(r["notional"] for r in rs)
        tds = [r["last_trans"] for r in rs if r["last_trans"]]
        ev = Event(cik, ticker, filed, sh, notional, max(tds) if tds else None, len(rs))
        if ev.vwap < minpx:
            funnel["price_floor"] += 1
            continue
        events.append(ev)
    funnel["events"] = len(events)
    return events


# ----------------------------------------------------------------------------
# Step 2. Prices (A5). One shape for every provider.
# ----------------------------------------------------------------------------

@dataclasses.dataclass
class Series:
    dates: list[dt.date]
    tr_open: list[float]     # open, adjusted for splits and dividends
    nominal: list[float]     # close as it printed on the day
    notional: list[float]    # close x volume, USD

    def __len__(self) -> int:
        return len(self.dates)


class PriceProvider:
    name = "abstract"
    keeps_delisted = False

    def daily(self, ticker: str) -> Series | None:
        """None means the provider answered and has no such security.
        Raises Transient when it did not answer."""
        raise NotImplementedError


def _window() -> tuple[dt.date, dt.date]:
    s = dt.date.fromisoformat(BASE["span_start"]) - dt.timedelta(days=160)
    e = min(dt.date.today(), dt.date.fromisoformat(BASE["span_end"]) + dt.timedelta(days=40))
    return s, e


class YahooProvider(PriceProvider):
    """Free. OMITS most delisted names, which is why A6 exists."""
    name = "yahoo"
    keeps_delisted = False

    def __init__(self, cache: pathlib.Path, pause: float = 0.35, tries: int = 4):
        self.cache = cache
        self.pause = pause
        self.tries = tries
        cache.mkdir(parents=True, exist_ok=True)

    def _raw(self, sym: str) -> dict | None:
        f = self.cache / f"{sym}.json"
        if f.exists():
            try:
                return json.loads(f.read_text()) or None
            except json.JSONDecodeError:
                f.unlink()                       # a write cut short; fetch it again
        s, e = _window()
        p1 = int(dt.datetime(s.year, s.month, s.day, tzinfo=dt.timezone.utc).timestamp())
        p2 = int(dt.datetime(e.year, e.month, e.day, tzinfo=dt.timezone.utc).timestamp()) + 86400
        url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
               f"?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true")
        status, body = http_get(url, BROWSER_UA, pause=self.pause, tries=self.tries, timeout=25)
        try:
            data = json.loads(body.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            raise Transient(f"yahoo {sym}: unparseable body, HTTP {status}")
        chart = data.get("chart") or {}
        res = (chart.get("result") or [None])[0]
        if res is None:
            code = ((chart.get("error") or {}).get("code") or "").lower()
            if status in (400, 404) or "not found" in code:
                f.write_text("null")
                return None
            raise Transient(f"yahoo {sym}: HTTP {status} {code}")
        if not res.get("timestamp"):
            f.write_text("null")                 # listed, but nothing in the window
            return None
        ind = res.get("indicators") or {}
        q = (ind.get("quote") or [{}])[0]
        adj = ((ind.get("adjclose") or [{}])[0]).get("adjclose")
        n = len(res["timestamp"])
        if adj is None or any(len(q.get(k) or []) != n for k in ("open", "close", "volume")) or len(adj) != n:
            raise Transient(f"yahoo {sym}: malformed series")
        f.write_text(json.dumps(res))
        return res

    def daily(self, ticker: str) -> Series | None:
        res = self._raw(ticker.replace(".", "-"))
        if res is None:
            return None
        ts = res["timestamp"]
        ind = res["indicators"]
        q = ind["quote"][0]
        adj = ind["adjclose"][0]["adjclose"]
        off = int((res.get("meta") or {}).get("gmtoffset") or 0)
        splits = []
        for ev in ((res.get("events") or {}).get("splits") or {}).values():
            try:
                d = dt.datetime.fromtimestamp(int(ev["date"]) + off, dt.timezone.utc).date()
                splits.append((d, float(ev["numerator"]) / float(ev["denominator"])))
            except (KeyError, ValueError, ZeroDivisionError, TypeError):
                continue
        out = Series([], [], [], [])
        for i, t in enumerate(ts):
            o, c, v, a = q["open"][i], q["close"][i], q["volume"][i], adj[i]
            if None in (o, c, a) or c <= 0 or o <= 0 or a <= 0:
                continue
            d = dt.datetime.fromtimestamp(int(t) + off, dt.timezone.utc).date()
            unsplit = 1.0
            for sd, ratio in splits:
                if sd > d:
                    unsplit *= ratio
            out.dates.append(d)
            out.tr_open.append(o * a / c)
            out.nominal.append(c * unsplit)
            out.notional.append(c * float(v or 0))
        return out if len(out) else None


class EodhdProvider(PriceProvider):
    """Subscription. The vendor's own page states that delisted tickers keep
    their history. UNTESTED against a live key at the time of writing."""
    name = "eodhd"
    keeps_delisted = True

    def __init__(self, key: str, cache: pathlib.Path, pause: float = 0.05):
        if os.environ.get("EODHD_CONTRACT_READ", "") != "volume-is-unadjusted":
            raise refuse("eodhd_contract_unread",
                         "this provider was written from recollection. Whether EODHD's "
                         "'volume' is adjusted for splits decides the liquidity bucket, and "
                         "so the cost, of every name that later split. Read the vendor's "
                         "field definitions; if volume is raw, set "
                         "EODHD_CONTRACT_READ=volume-is-unadjusted; if it is adjusted, the "
                         "notional line below must un-adjust it first.")
        self.key, self.cache, self.pause = key, cache, pause
        cache.mkdir(parents=True, exist_ok=True)

    def daily(self, ticker: str) -> Series | None:
        sym = ticker.replace(".", "-")
        f = self.cache / f"{sym}.json"
        rows = None
        if f.exists():
            try:
                rows = json.loads(f.read_text())
            except json.JSONDecodeError:
                f.unlink()
        if rows is None:
            s, e = _window()
            url = (f"https://eodhd.com/api/eod/{urllib.parse.quote(sym)}.US?from={s}&to={e}"
                   f"&period=d&fmt=json&api_token={self.key}")
            status, body = http_get(url, BROWSER_UA, pause=self.pause)
            if status == 404:
                rows = []
            else:
                try:
                    rows = json.loads(body.decode("utf-8", "replace"))
                except json.JSONDecodeError:
                    raise Transient(f"eodhd {sym}: unparseable body, HTTP {status}")
                if not isinstance(rows, list):
                    raise Transient(f"eodhd {sym}: {str(rows)[:120]}")
            f.write_text(json.dumps(rows))
        out = Series([], [], [], [])
        for r in rows:
            try:
                d = dt.date.fromisoformat(str(r["date"])[:10])
                o, c, a, v = float(r["open"]), float(r["close"]), float(r["adjusted_close"]), float(r["volume"] or 0)
            except (KeyError, ValueError, TypeError):
                continue
            if o <= 0 or c <= 0 or a <= 0:
                continue
            out.dates.append(d)
            out.tr_open.append(o * a / c)
            out.nominal.append(c)
            out.notional.append(c * v)
        return out if len(out) else None


class CsvProvider(PriceProvider):
    """<root>/<TICKER>.csv with date,open,close,adj_close,volume, close being
    nominal. For tests and for any local archive."""
    name = "csv"

    def __init__(self, root: str, keeps_delisted: bool = False):
        self.root = pathlib.Path(root)
        self.keeps_delisted = keeps_delisted

    def daily(self, ticker: str) -> Series | None:
        f = self.root / f"{ticker}.csv"
        if not f.exists():
            return None
        out = Series([], [], [], [])
        for r in csv.DictReader(f.open()):
            o, c, a, v = float(r["open"]), float(r["close"]), float(r["adj_close"]), float(r["volume"])
            out.dates.append(dt.date.fromisoformat(r["date"][:10]))
            out.tr_open.append(o * a / c)
            out.nominal.append(c)
            out.notional.append(c * v)
        return out if len(out) else None


# ----------------------------------------------------------------------------
# Step 3. The measurement
# ----------------------------------------------------------------------------

@dataclasses.dataclass
class Trade:
    ticker: str
    cik: str
    filed: dt.date
    entry_date: dt.date
    exit_date: dt.date
    gross_bps: float
    bench_bps: dict
    adv_usd: float
    bucket: str
    cost_mid: float | None
    cost_cons: float | None
    n_accessions: int


def bucket_of(adv: float) -> tuple[str, float | None, float | None]:
    for label, lo, mid, cons in PROTOCOL2["A3_cost_tiers_bps"]:
        if adv >= lo:
            return label, mid, cons
    return "B5 <$1m", None, None


def median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


DROPS = ("no_prices", "provider_error", "no_entry_bar", "truncated_horizon",
         "insufficient_history", "liquidity_floor", "identity_unscorable",
         "identity_mismatch", "overlap_skipped", "benchmark_missing")


def measure(events: Sequence[Event], prov: PriceProvider, delisted: set[str],
            only: set[str] | None = None) -> tuple[list[Trade], dict]:
    h = BASE["horizon_sessions"]
    minliq = BASE["min_median_notional_usd"]
    W, WMIN = PROTOCOL2["A5_liquidity_window_sessions"], PROTOCOL2["A5_liquidity_min_sessions"]
    lo_r, hi_r = PROTOCOL2["A5_identity_ratio"]

    bench: dict[str, dict[dt.date, float]] = {}
    for b in PROTOCOL2["A1_benchmarks"]:
        try:
            s = prov.daily(b)
        except Transient as err:
            raise refuse("benchmark_unavailable", f"{prov.name} did not answer for {b}: {err}")
        if s is None:
            raise refuse("benchmark_unavailable", f"{prov.name} has no series for {b}")
        bench[b] = dict(zip(s.dates, s.tr_open))

    by_ticker: dict[str, list[Event]] = {}
    for e in events:
        if only is None or e.ticker in only:
            by_ticker.setdefault(e.ticker, []).append(e)

    drop = {k: 0 for k in DROPS}
    cov = {"tickers": len(by_ticker), "tickers_priced": 0, "tickers_absent": 0,
           "tickers_provider_error": 0, "events_in": sum(len(v) for v in by_ticker.values()),
           "no_prices_delisted_issuer": 0, "truncated_delisted_issuer": 0}
    cands: list[Trade] = []

    for i, (ticker, evs) in enumerate(sorted(by_ticker.items()), 1):
        if i % 250 == 0:
            print(f"    priced {i:,}/{len(by_ticker):,} tickers, candidates {len(cands):,}", flush=True)
        try:
            s = prov.daily(ticker)
        except Transient as err:
            cov["tickers_provider_error"] += 1
            drop["provider_error"] += len(evs)
            print(f"    provider error: {err}", flush=True)
            continue
        if s is None:
            cov["tickers_absent"] += 1
            drop["no_prices"] += len(evs)
            cov["no_prices_delisted_issuer"] += sum(1 for e in evs if e.cik in delisted)
            continue
        cov["tickers_priced"] += 1
        idx = {d: k for k, d in enumerate(s.dates)}
        for e in sorted(evs, key=lambda x: x.filed):
            k = next((j for j, d in enumerate(s.dates) if d > e.filed), None)
            if k is None:
                drop["no_entry_bar"] += 1
                cov["truncated_delisted_issuer"] += e.cik in delisted
                continue
            if k + h >= len(s):
                drop["truncated_horizon"] += 1
                cov["truncated_delisted_issuer"] += e.cik in delisted
                continue
            if k < WMIN:
                drop["insufficient_history"] += 1
                continue
            adv = median(s.notional[max(0, k - W):k])
            if adv < minliq:
                drop["liquidity_floor"] += 1
                continue
            j = None
            if e.last_trans is not None and e.last_trans <= e.filed:
                j = idx.get(e.last_trans)
                if j is None:
                    prior = [m for m, d in enumerate(s.dates)
                             if d < e.last_trans and (e.last_trans - d).days <= 5]
                    j = prior[-1] if prior else None
            if j is None:
                drop["identity_unscorable"] += 1
                continue
            ratio = e.vwap / s.nominal[j]
            if not (lo_r <= ratio <= hi_r):
                drop["identity_mismatch"] += 1
                continue
            d_in, d_out = s.dates[k], s.dates[k + h]
            if any(d_in not in bench[b] or d_out not in bench[b] for b in bench):
                drop["benchmark_missing"] += 1
                continue
            gross = (s.tr_open[k + h] / s.tr_open[k] - 1.0) * 1e4
            bb = {b: (bench[b][d_out] / bench[b][d_in] - 1.0) * 1e4 for b in bench}
            label, mid, cons = bucket_of(adv)
            cands.append(Trade(ticker, e.cik, e.filed, d_in, d_out, gross, bb, adv,
                                label, mid, cons, e.n_accessions))
    trades: list[Trade] = []
    open_until: dict[str, dt.date] = {}
    for t in sorted(cands, key=lambda t: (t.cik, t.entry_date, t.filed, t.ticker)):
        if t.cik in open_until and t.entry_date <= open_until[t.cik]:
            drop["overlap_skipped"] += 1
            continue
        open_until[t.cik] = t.exit_date
        trades.append(t)
    trades.sort(key=lambda t: (t.entry_date, t.ticker))
    return trades, {"dropped": drop, "coverage": cov}


# ----------------------------------------------------------------------------
# Step 4. Statistics and the verdict
# ----------------------------------------------------------------------------

def t_crit(df: int) -> float:
    """Two-sided 95% Student t quantile, by the Cornish-Fisher series in 1/df.
    Accurate to the third decimal for df >= 9, which is the only range used."""
    z = 1.959964
    return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
            + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))


def summarise(xs: Sequence[float], clusters: Sequence[object]) -> dict:
    n = len(xs)
    if n == 0:
        return {"n": 0, "scorable": False, "why": "no trades"}
    mean = sum(xs) / n
    sums: dict[object, float] = {}
    for x, c in zip(xs, clusters):
        sums[c] = sums.get(c, 0.0) + (x - mean)
    G = len(sums)
    s = sorted(xs)
    k = int(n * 0.01)
    trimmed = s[k:n - k] if n - 2 * k > 0 else s
    out = {"n": n, "clusters": G, "mean_bps": round(mean, 2),
           "median_bps": round(median(xs), 2),
           "trimmed_1pct_mean_bps": round(sum(trimmed) / len(trimmed), 2),
           "share_positive": round(sum(1 for x in xs if x > 0) / n, 4)}
    if n > 1:
        out["sd_bps"] = round((sum((x - mean) ** 2 for x in xs) / (n - 1)) ** 0.5, 1)
    if G < 10:
        out.update(scorable=False, why=f"{G} monthly clusters, fewer than 10")
        return out
    se = (G / (G - 1) * sum(v * v for v in sums.values())) ** 0.5 / n
    tc = t_crit(G - 1)
    out.update(scorable=True, se_bps=round(se, 2), mean_exact=mean, lo_exact=mean - tc * se,
               ci95_bps=[round(mean - tc * se, 2), round(mean + tc * se, 2)],
               t_stat=round(mean / se, 2) if se else None)
    return out


def _month(t: Trade) -> tuple[int, int]:
    return (t.entry_date.year, t.entry_date.month)


def block(trades: Sequence[Trade], cost) -> dict:
    """One population under one cost rule, raw and against each benchmark."""
    ts = [t for t in trades if cost(t) is not None]
    cl = [_month(t) for t in ts]
    out = {"raw_net": summarise([t.gross_bps - cost(t) for t in ts], cl)}
    for b in PROTOCOL2["A1_benchmarks"]:
        out[f"abnormal_net_vs_{b}"] = summarise([t.gross_bps - t.bench_bps[b] - cost(t) for t in ts], cl)
    return out


def lower(blk: dict) -> float | None:
    los = []
    for b in PROTOCOL2["A1_benchmarks"]:
        s = blk[f"abnormal_net_vs_{b}"]
        if not s.get("scorable"):
            return None
        los.append(s["lo_exact"])
    return min(los)


FLAT = lambda t: BASE["round_trip_cost_bps"]            # noqa: E731
TIER_MID = lambda t: t.cost_mid                          # noqa: E731
TIER_CONS = lambda t: t.cost_cons                        # noqa: E731
ZERO = lambda t: 0.0                                     # noqa: E731
BRANCHES = ["KILL", "COST-DETERMINED", "BEATS A TRACKER", "PAYS FOR ITSELF"]


def in_pop(t: Trade, name: str) -> bool:
    return t.bucket[:2] in PROTOCOL2["T_populations"][name]


def time_hurdle(trades_per_year: float) -> float | None:
    """The net edge per trade at which a population pays GBP 15,000 a year of
    time. 29.8 bp when it fills the book; higher when it cannot, because idle
    slots earn the tracker and nothing more."""
    used = min(trades_per_year, PROTOCOL2["trades_per_year_at_full_book"])
    if used <= 0:
        return None
    return PROTOCOL2["time_cost_gbp"] / (used * PROTOCOL2["slot_notional_gbp"] / 1e4)


def branch(trades: Sequence[Trade], span_years: float) -> tuple[str | None, dict]:
    LG = lower(block(trades, FLAT))
    d: dict = {"n": len(trades), "L_G_bps": LG, "T": {}}
    for name in PROTOCOL2["T_populations"]:
        pop = [t for t in trades if in_pop(t, name)]
        tpy = len(pop) / span_years
        d["T"][name] = {"n": len(pop), "trades_per_year": round(tpy, 1),
                        "L_T_bps": lower(block(pop, TIER_MID)), "time_hurdle_bps": time_hurdle(tpy)}
    if LG is None:
        return None, d
    if LG <= 0:
        return "KILL", d
    best: tuple[str, str] | None = None
    for name, v in d["T"].items():
        if v["L_T_bps"] is None:
            continue
        b = ("COST-DETERMINED" if v["L_T_bps"] <= 0
             else "BEATS A TRACKER" if v["L_T_bps"] < v["time_hurdle_bps"] else "PAYS FOR ITSELF")
        v["branch"] = b
        if best is None or BRANCHES.index(b) > BRANCHES.index(best[0]):
            best = (b, name)
    if best is None:
        return None, d
    d["deciding_population"] = best[1]
    return best[0], d


def flip_threshold(stat: dict, m: int) -> float | None:
    """The mean the m unpriced events would need for the lower bound to reach
    zero, holding the half-width. Approximate, and reported as such."""
    if not stat.get("scorable") or m <= 0:
        return None
    n, mean = stat["n"], stat["mean_exact"]
    hw = mean - stat["lo_exact"]
    return ((n + m) * hw - n * mean) / m


def verdict(trades: Sequence[Trade], prov: PriceProvider, span_years: float = 3.65,
            unpriced: int = 0, lost_delisted: int = 0) -> dict:
    """The decision rule of the amendment, section 3, and A6's two readings.

    unpriced       events the provider had no series for: an upper bound on
                   the trades a partial archive is missing.
    lost_delisted  events lost, unpriced or cut short, on an issuer the
                   delisting register names.
    """
    cap = PROTOCOL2["tail_rule_abs_gross_pct"] * 100.0
    full, d_full = branch(trades, span_years)
    core = [t for t in trades if abs(t.gross_bps) <= cap]
    trim, d_trim = branch(core, span_years)
    out: dict = {"all_trades": {"branch": full, **d_full},
                 "without_tail": {"branch": trim, **d_trim, "excluded": len(trades) - len(core)}}
    if full is None or (trim is None and full != "KILL"):
        out["verdict"] = "UNSCORABLE"
        out["text"] = "UNSCORABLE. An interval could not be formed; see the statistics for the reason."
        return out
    final = full if trim is None else min(full, trim, key=BRANCHES.index)
    tail = trim is not None and full != trim
    basis, d = (trades, d_full) if final == full else (core, d_trim)
    n = len(basis)
    surv: dict = {"unpriced_events": unpriced, "events_lost_on_delisted_issuers": lost_delisted}
    why = ""
    if final == "KILL":
        provisional = False
        if not prov.keeps_delisted and unpriced > 0:
            g = block(basis, FLAT)
            ths = [flip_threshold(g[f"abnormal_net_vs_{b}"], unpriced) for b in PROTOCOL2["A1_benchmarks"]]
            need = max(x for x in ths if x is not None)
            surv["mean_bps_unpriced_events_would_need"] = round(need, 1)
            if need <= PROTOCOL2["A6_kill_stands_if_unpriced_would_need_bps"]:
                provisional = True
                why = (f"the {unpriced:,} unpriced events would need to average only {need:.0f} bp to "
                       f"reverse it, and {prov.name} omits delisted names")
    else:
        if final == "COST-DETERMINED":
            L, pop_n = d["L_G_bps"], n
        else:
            t = d["T"][d["deciding_population"]]
            L, pop_n = t["L_T_bps"], t["n"]
        shift = lost_delisted * 1e4 / (pop_n + lost_delisted) if lost_delisted else 0.0
        surv["bound_if_every_delisted_loss_were_total_bps"] = round(L - shift, 1)
        provisional = not prov.keeps_delisted or (L - shift) <= 0
        if not prov.keeps_delisted:
            why = (f"{prov.name} omits delisted names, so this licenses a re-run on an archive that "
                   "keeps them and nothing else")
        elif provisional:
            why = (f"charging the {lost_delisted:,} events lost on delisted issuers a total loss "
                   "takes the bound to zero or below")
    out.update(verdict=final, tail_dependent=tail, provisional=provisional, survivorship=surv)
    if "deciding_population" in d and final not in ("KILL", "COST-DETERMINED"):
        out["deciding_population"] = d["deciding_population"]
    text = final
    if out.get("deciding_population"):
        text += f" on {out['deciding_population']}"
    if tail:
        text += f" (TAIL-DEPENDENT: {full} with the tail, {trim} without it)"
    if provisional:
        text += f". PROVISIONAL: {why}"
    out["text"] = text + "."
    return out


def registered_s0(trades: Sequence[Trade]) -> dict:
    """The statistic exactly as registered on 19 September, read by that rule.
    Reported beside the amended one, and labelled for what it is."""
    s = summarise([t.gross_bps - BASE["round_trip_cost_bps"] for t in trades], [_month(t) for t in trades])
    naive = None
    if s["n"] > 1:
        se = s["sd_bps"] / s["n"] ** 0.5
        naive = [round(s["mean_bps"] - 1.959964 * se, 2), round(s["mean_bps"] + 1.959964 * se, 2)]
        H = BASE["hurdles_bps_at_h5"]
        lo = naive[0]
        s["branch_19_sep_rule"] = ("(a)" if lo <= 0 else "(b)" if lo < H["tracker_7pct"]
                                   else "(c)" if lo < H["tracker_plus_time"] else "(d)")
    s["ci95_naive_iid_bps"] = naive
    s["note"] = ("RAW return, market included. A rising market passes this with no "
                 "edge; amendment A1 is why it no longer decides anything.")
    return s


def analyse(trades: Sequence[Trade], meta: dict, prov: PriceProvider) -> dict:
    span_years = max(1e-9, (meta["span_end_effective"] - meta["span_start"]).days / 365.25)
    cov, drop = meta["coverage"], meta["dropped"]
    stats: dict = {
        "stamp": STAMP, "protocol_hash": protocol_hash(), "code_sha256": code_hash(),
        "provider": prov.name, "provider_keeps_delisted": prov.keeps_delisted,
        "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "span": [str(meta["span_start"]), str(meta["span_end_effective"])],
        "span_years": round(span_years, 3), "trades": len(trades),
        "G_all_trades_flat_cost": block(trades, FLAT),
        "T_B1_to_B4_tiered_midpoint": block([t for t in trades if in_pop(t, "B1-B4")], TIER_MID),
        "T_B1_to_B2_tiered_midpoint": block([t for t in trades if in_pop(t, "B1-B2")], TIER_MID),
        "B1_to_B4_tiered_conservative": block([t for t in trades if in_pop(t, "B1-B4")], TIER_CONS),
        "gross_all_trades": block(trades, ZERO),
        "registered_19_sep_statistic": registered_s0(trades),
    }
    per: dict = {}
    for label in [t[0] for t in PROTOCOL2["A3_cost_tiers_bps"]] + ["B5 <$1m"]:
        ts = [t for t in trades if t.bucket == label]
        per[label] = {"trades_per_year": round(len(ts) / span_years, 1),
                      "cost_mid_bps": ts[0].cost_mid if ts else None,
                      "cost_cons_bps": ts[0].cost_cons if ts else None,
                      "gross": block(ts, ZERO)}
    stats["by_bucket_gross"] = per
    stats["by_entry_year_mean_gross_abnormal"] = {
        str(y): {b: summarise([t.gross_bps - t.bench_bps[b] for t in trades if t.entry_date.year == y],
                              [_month(t) for t in trades if t.entry_date.year == y]).get("mean_bps")
                 for b in PROTOCOL2["A1_benchmarks"]}
        | {"n": sum(1 for t in trades if t.entry_date.year == y)}
        for y in sorted({t.entry_date.year for t in trades})}
    lost = cov["no_prices_delisted_issuer"] + cov["truncated_delisted_issuer"]
    stats["verdict"] = verdict(trades, prov, span_years, drop["no_prices"], lost)
    arith = {}
    for name, key in (("B1-B4", "T_B1_to_B4_tiered_midpoint"), ("B1-B2", "T_B1_to_B2_tiered_midpoint")):
        means = [stats[key][f"abnormal_net_vs_{b}"].get("mean_bps") for b in PROTOCOL2["A1_benchmarks"]]
        n_pop = stats[key]["raw_net"]["n"]
        if n_pop and all(x is not None for x in means):
            used = min(n_pop / span_years, PROTOCOL2["trades_per_year_at_full_book"])
            gbp = used * PROTOCOL2["slot_notional_gbp"] * min(means) / 1e4
            arith[name] = {"trades_per_year_used": round(used, 1),
                           "gbp_per_year_over_a_tracker": round(gbp),
                           "gbp_per_year_after_time": round(gbp - PROTOCOL2["time_cost_gbp"])}
    stats["arithmetic_at_registered_book"] = {
        "note": "sixteen slots of GBP 6,250; the POINT estimate on the lower benchmark reading; "
                "arithmetic and not a forecast", **arith}
    return stats


def code_hash() -> str:
    return hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()[:16]


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

def _row(label: str, s: dict) -> str:
    if not s.get("n"):
        return f"| {label} | 0 | n/a | n/a | n/a | n/a |"
    ci = s.get("ci95_bps")
    return (f"| {label} | {s['n']:,} | {s['mean_bps']:.1f} | "
            f"{'%.1f to %.1f' % tuple(ci) if ci else 'refused: ' + s.get('why', '')} | "
            f"{s['median_bps']:.1f} | {s['share_positive']:.1%} |")


def _bp(x) -> str:
    return "n/a" if x is None else f"{x:.1f}"


def render(stats: dict, meta: dict) -> str:
    v = stats["verdict"]
    a = v["all_trades"]
    L = ["# Insider-purchase kill test: result", "",
         f"**{STAMP}** Protocol hash `{stats['protocol_hash']}`, code `{stats['code_sha256']}`. "
         f"Provider `{stats['provider']}`. Span {stats['span'][0]} to {stats['span'][1]}. Run {stats['run_at']}.", "",
         "## Verdict", "", f"**{v['text']}**", "",
         f"- L(G), all {a['n']:,} trades at flat 15.7 bp: {_bp(a['L_G_bps'])} bp"]
    for name, t in a["T"].items():
        L.append(f"- L(T) on {name} at tiered midpoint cost: {_bp(t['L_T_bps'])} bp over {t['n']:,} trades "
                 f"({t['trades_per_year']} a year; time hurdle {_bp(t['time_hurdle_bps'])} bp)"
                 + (f": {t['branch']}" if "branch" in t else ""))
    L += [f"- Without the tail ({v['without_tail']['excluded']} trades over 100% in five sessions): "
          f"{v['without_tail']['branch']}",
          f"- Survivorship: {json.dumps(v.get('survivorship', {}))}", "",
          "## Net abnormal return per trade, bp", "",
          "| Population and cost | n | mean | 95% interval | median | share positive |", "|---|---|---|---|---|---|"]
    for key, name in (("G_all_trades_flat_cost", "G: all, flat 15.7"),
                      ("T_B1_to_B4_tiered_midpoint", "T: B1 to B4, tiered midpoint"),
                      ("T_B1_to_B2_tiered_midpoint", "T: B1 to B2, tiered midpoint"),
                      ("B1_to_B4_tiered_conservative", "B1 to B4, tiered conservative"),
                      ("gross_all_trades", "all, no cost")):
        for b in PROTOCOL2["A1_benchmarks"]:
            L.append(_row(f"{name}, vs {b}", stats[key][f"abnormal_net_vs_{b}"]))
    L += ["", "## Gross abnormal return by liquidity bucket, bp", "",
          "| Bucket | trades a year | cost mid / cons | n | mean vs SPY | 95% interval | mean vs IWM | 95% interval |",
          "|---|---|---|---|---|---|---|---|"]
    for label, p in stats["by_bucket_gross"].items():
        x, y = p["gross"]["abnormal_net_vs_SPY"], p["gross"]["abnormal_net_vs_IWM"]
        f = lambda s: ("%.1f to %.1f" % tuple(s["ci95_bps"])) if s.get("ci95_bps") else "n/a"   # noqa: E731
        m = lambda s: ("%.1f" % s["mean_bps"]) if s.get("n") else "n/a"                          # noqa: E731
        cost = f"{p['cost_mid_bps']} / {p['cost_cons_bps']}" if p["cost_mid_bps"] else "flat only"
        L.append(f"| {label} | {p['trades_per_year']} | {cost} | {x.get('n', 0):,} | {m(x)} | {f(x)} | {m(y)} | {f(y)} |")
    s0 = stats["registered_19_sep_statistic"]
    L += ["", "## The statistic as registered on 19 September", "",
          f"Raw net return at flat 15.7 bp: n = {s0.get('n')}, mean {s0.get('mean_bps')} bp, "
          f"naive interval {s0.get('ci95_naive_iid_bps')}, branch {s0.get('branch_19_sep_rule')}. {s0['note']}", "",
          "## Coverage and what was dropped", "",
          f"- Funnel: {json.dumps(meta['funnel'])}",
          f"- Coverage: {json.dumps(meta['coverage'])}",
          f"- Dropped: {json.dumps(meta['dropped'])}",
          f"- By entry year, mean gross abnormal: {json.dumps(stats['by_entry_year_mean_gross_abnormal'])}",
          f"- Arithmetic: {json.dumps(stats['arithmetic_at_registered_book'])}",
          "", "## What this does not license", "",
          "No capital, no calibration and no §13 reading. Market impact is in no cost figure here "
          "(§13 row 37). The cost tiers are the registered table and are themselves unmeasured (§13 row 36)."]
    return "\n".join(L) + "\n"


def load_delisted(register: pathlib.Path) -> set[str]:
    if not register.exists():
        raise refuse("delisting_register_absent", f"{register} does not exist")
    ciks = set()
    with register.open() as f:
        for row in csv.DictReader((ln for ln in f if not ln.startswith("#")), delimiter="\t"):
            if row.get("form") in {"25", "25-NSE"}:
                ciks.add(row["cik"].lstrip("0"))
    if not ciks:
        raise refuse("delisting_register_empty", f"{register} names no Form 25 or 25-NSE issuer")
    return ciks


PROBE_LIVE = ("SPY", "IWM", "AAPL", "KO", "NVDA", "WMT", "BRK.B")
PROBE_GONE = ("ATVI", "VMW", "SPLK", "SGEN", "HZNP", "SIVB", "FRC", "PXD")


def probe(prov: PriceProvider, out: pathlib.Path) -> None:
    """First contact with a price provider, on names chosen for what is publicly
    known about them and on no insider event at all. It answers three questions
    the harness otherwise takes on trust: does the provider answer this machine,
    is a split un-adjusted in the right direction, and does it keep a name after
    the name stops trading. No event return is computed, so this is not a look.

    NVDA split ten for one with effect from 2024-06-10 and closed the session
    before near USD 1,209 (recollection, which is why it is printed and why the
    pass band is wide). The eight in PROBE_GONE were acquired or failed inside
    the span."""
    rep_: dict = {"provider": prov.name, "live": {}, "gone": {}, "checks": {}}
    deaf = 0
    for tk in PROBE_LIVE + PROBE_GONE:
        try:
            if deaf >= 2:
                raise Transient("not asked: the first two questions went unanswered")
            s_ = prov.daily(tk)
        except Transient as err:
            deaf += 1
            row = {"answered": False, "error": str(err)[:160]}
        else:
            row = {"answered": True, "present": s_ is not None}
            if s_ is not None:
                row.update(bars=len(s_), first=str(s_.dates[0]), last=str(s_.dates[-1]))
        (rep_["live"] if tk in PROBE_LIVE else rep_["gone"])[tk] = row
        print(f"  {tk:<6} {row}", flush=True)
    c = rep_["checks"]
    c["every_live_name_answered_and_present"] = all(r.get("present") for r in rep_["live"].values())
    c["every_question_answered"] = all(r["answered"] for r in list(rep_["live"].values()) + list(rep_["gone"].values()))
    c["gone_names_kept"] = sum(1 for r in rep_["gone"].values() if r.get("present"))
    c["gone_names_asked"] = len(PROBE_GONE)
    try:
        nv = prov.daily("NVDA")
        k = nv.dates.index(dt.date(2024, 6, 7))
        c["nvda_nominal_close_2024_06_07"] = round(nv.nominal[k], 2)
        c["nvda_tr_open_2024_06_07"] = round(nv.tr_open[k], 2)
        c["split_unadjusted_in_the_right_direction"] = 1100.0 <= nv.nominal[k] <= 1300.0
        ko = prov.daily("KO")
        c["ko_tr_open_below_nominal_at_start"] = ko.tr_open[0] < ko.nominal[0]
    except (AttributeError, ValueError, Transient) as err:
        c["split_unadjusted_in_the_right_direction"] = False
        c["probe_error"] = str(err)[:160]
    rep_["pass"] = bool(c["every_live_name_answered_and_present"] and c["every_question_answered"]
                        and c["split_unadjusted_in_the_right_direction"] and c.get("ko_tr_open_below_nominal_at_start"))
    (out / "provider_probe.json").write_text(json.dumps(rep_, indent=1))
    notice("probe rows", {k: (("present %s..%s n=%s" % (v["first"], v["last"], v["bars"])) if v.get("present")
                              else "absent" if v["answered"] else "UNANSWERED " + v.get("error", "")[:60])
                          for k, v in {**rep_["live"], **rep_["gone"]}.items()})
    notice("probe checks", {**c, "pass": rep_["pass"]})
    print(f"  checks {json.dumps(c)}")
    print(f"  PROBE {'PASSED' if rep_['pass'] else 'FAILED'}: {prov.name}")
    if not rep_["pass"]:
        raise refuse("provider_probe_failed", f"{prov.name} did not behave as the harness assumes; see provider_probe.json")


def check_contiguous(present: Sequence[str], start: dt.date, end: dt.date) -> None:
    """A quarter missing at the END of the span shortens the span. One missing
    anywhere else would leave a hole the statistics could not see."""
    qs = quarters(start, end)
    have = [q for q in qs if q in set(present)]
    if not have or have != qs[:len(have)]:
        raise refuse("event_archive_gap",
                     f"archives present {sorted(present)} do not run unbroken from {qs[0]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=["yahoo", "eodhd", "csv"], default="yahoo")
    ap.add_argument("--csv-root", default="prices")
    ap.add_argument("--csv-keeps-delisted", action="store_true")
    ap.add_argument("--archives", default=None, help="directory of *_form345.zip; skips the SEC fetch")
    ap.add_argument("--register", default=None, help="the delisting register; there is no default and its absence refuses")
    ap.add_argument("--probe", action="store_true",
                    help="first contact with the price provider on well-known names; touches no SEC host and no event")
    ap.add_argument("--cache", default=".mvm2_cache")
    ap.add_argument("--out", default="out")
    ap.add_argument("--smoke", type=int, default=None,
                    help="price a seeded sample of N tickers and report COVERAGE ONLY; no return is computed into any output")
    a = ap.parse_args()
    if a.smoke is not None and a.smoke < 1:
        raise refuse("smoke_size", "--smoke takes a positive count; nought is not a smoke run")
    if a.probe:
        out_ = pathlib.Path(a.out)
        out_.mkdir(parents=True, exist_ok=True)
        print(f"PROVIDER PROBE ({a.provider}); protocol hash {protocol_hash()}, code {code_hash()}")
        prov_ = make_provider(a, pathlib.Path(a.cache))
        if isinstance(prov_, YahooProvider):
            prov_.tries = 2                         # a probe that waits is not a probe
        probe(prov_, out_)
        return
    if not a.register:
        raise refuse("delisting_register_absent", "--register is required; there is no default path")

    start = dt.date.fromisoformat(BASE["span_start"])
    end = dt.date.fromisoformat(BASE["span_end"])
    cache = pathlib.Path(a.cache)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("INSIDER-PURCHASE KILL TEST (mvm2) - NON-EVIDENTIARY")
    print(f"protocol hash {protocol_hash()}, code {code_hash()}; amendment fixed "
          f"{PROTOCOL2['amended_on']} before any price was fetched")
    print("=" * 78)

    print("\n[1/4] event archives")
    if a.archives:
        paths = sorted(pathlib.Path(a.archives).glob("*_form345.zip"))
        manifest = [{"quarter": p.name[:6], "bytes": p.stat().st_size, "source": "local",
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    else:
        paths, manifest = fetch_datasets(start, end, cache / "sec")
    check_contiguous([m["quarter"] for m in manifest], start, end)
    (out / "input_manifest.json").write_text(json.dumps(manifest, indent=1))

    print("\n[2/4] events")
    funnel = new_funnel()
    records: list[dict] = []
    for p in paths:
        records += parse_archive(p, funnel)
    events = build_events(records, start, end, funnel)
    if not events:
        raise refuse("no_events", f"the archives produced no qualifying event: {funnel}")
    last_q = max(m["quarter"] for m in manifest)
    q_end = dt.date(int(last_q[:4]), int(last_q[5]) * 3, 1) + dt.timedelta(days=31)
    q_end = q_end.replace(day=1) - dt.timedelta(days=1)
    span_end_eff = min(end, q_end)
    for k, v in funnel.items():
        print(f"  {k:<28} {v:,}")
    with (out / "events.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cik", "ticker", "filed", "shares", "notional_usd", "vwap", "last_trans", "n_accessions"])
        for e in events:
            w.writerow([e.cik, e.ticker, e.filed, f"{e.shares:.2f}", f"{e.notional:.2f}", f"{e.vwap:.4f}",
                        e.last_trans or "", e.n_accessions])

    print("\n[3/4] delisting register")
    delisted = load_delisted(pathlib.Path(a.register))
    print(f"  distinct delisted CIKs: {len(delisted):,}")

    prov = make_provider(a, cache)

    print(f"\n[4/4] pricing with {prov.name}")
    only = None
    if a.smoke is not None:
        tickers = sorted({e.ticker for e in events})
        random.Random(PROTOCOL2["smoke_seed"]).shuffle(tickers)
        only = set(tickers[:a.smoke])
        print(f"  SMOKE: {len(only)} of {len(tickers):,} tickers, drawn by seed {PROTOCOL2['smoke_seed']}")
    trades, meta = measure(events, prov, delisted, only)
    meta.update(funnel=funnel, span_start=start, span_end_effective=span_end_eff)
    cov = meta["coverage"]
    (out / "coverage.json").write_text(json.dumps(
        {"stamp": STAMP, "protocol_hash": protocol_hash(), "code_sha256": code_hash(), "provider": prov.name,
         "smoke": a.smoke is not None, "funnel": funnel, "coverage": cov, "dropped": meta["dropped"],
         "trades": len(trades), "span_end_effective": str(span_end_eff)}, indent=1))
    print(f"  coverage  {cov}")
    print(f"  dropped   {meta['dropped']}")
    print(f"  trades    {len(trades):,}")
    notice("funnel", funnel)
    notice("coverage", {"smoke": a.smoke is not None, "provider": prov.name, "coverage": cov,
                        "dropped": meta["dropped"], "trades": len(trades),
                        "span_end_effective": str(span_end_eff), "archives": len(manifest)})

    if a.smoke is not None:
        print("\n  SMOKE RUN: coverage only. No return was written or printed.")
        return
    err_share = cov["tickers_provider_error"] / max(1, cov["tickers"])
    if err_share > 0.02:
        raise refuse("provider_unreliable",
                     f"{err_share:.1%} of tickers went unanswered; a verdict over the remainder "
                     "would be a verdict over whatever the provider chose to return. Re-run: the cache resumes.")

    stats = analyse(trades, meta, prov)
    stats["funnel"], stats["coverage"], stats["dropped"] = funnel, cov, meta["dropped"]
    stats["protocol"] = {"base": BASE, "amendment": PROTOCOL2}
    (out / "killtest_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    with (out / "killtest_trades.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "cik", "filed", "entry_date", "exit_date", "gross_bps", "spy_bps", "iwm_bps",
                    "adv_usd", "bucket", "cost_mid_bps", "cost_cons_bps", "n_accessions"])
        for t in trades:
            w.writerow([t.ticker, t.cik, t.filed, t.entry_date, t.exit_date, f"{t.gross_bps:.2f}",
                        f"{t.bench_bps['SPY']:.2f}", f"{t.bench_bps['IWM']:.2f}", f"{t.adv_usd:.0f}",
                        t.bucket, t.cost_mid if t.cost_mid is not None else "",
                        t.cost_cons if t.cost_cons is not None else "", t.n_accessions])
    report = render(stats, meta)
    (out / "killtest_report.md").write_text(report)
    brief = lambda blk: {b: {k: blk[f"abnormal_net_vs_{b}"].get(k) for k in ("n", "clusters", "mean_bps", "ci95_bps", "median_bps", "share_positive")}   # noqa: E731
                         for b in PROTOCOL2["A1_benchmarks"]}
    notice("verdict", {"text": stats["verdict"]["text"], "hash": stats["protocol_hash"], "code": stats["code_sha256"],
                       "detail": stats["verdict"]})
    notice("net abnormal", {k: brief(stats[k]) for k in ("G_all_trades_flat_cost", "T_B1_to_B4_tiered_midpoint",
                                                         "T_B1_to_B2_tiered_midpoint", "gross_all_trades")})
    notice("gross by bucket", {k: {"per_year": v["trades_per_year"], **brief(v["gross"])}
                               for k, v in stats["by_bucket_gross"].items()})
    notice("registered and context", {"registered_19_sep": stats["registered_19_sep_statistic"],
                                      "by_year": stats["by_entry_year_mean_gross_abnormal"],
                                      "arithmetic": stats["arithmetic_at_registered_book"]})
    print("\n" + "=" * 78)
    print(report)


def make_provider(a: argparse.Namespace, cache: pathlib.Path) -> PriceProvider:
    if a.provider == "yahoo":
        return YahooProvider(cache / "px_yahoo")
    if a.provider == "eodhd":
        key = os.environ.get("EODHD_KEY", "").strip()
        if not key:
            raise refuse("eodhd_key_absent", "EODHD_KEY is unset")
        return EodhdProvider(key, cache / "px_eodhd")
    return CsvProvider(a.csv_root, a.csv_keeps_delisted)


FUNNEL_KEYS = ("submissions", "form4", "bad_filing_date", "malformed_rows", "p_rows",
               "p_rows_no_price_or_shares", "purchase_accessions", "not_officer_or_director",
               "duplicate_accession", "outside_span", "issuer_days", "bad_ticker", "price_floor", "events")


def new_funnel() -> dict:
    return {k: 0 for k in FUNNEL_KEYS}


if __name__ == "__main__":
    main()
