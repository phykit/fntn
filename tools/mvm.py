#!/usr/bin/env python3
"""
mvm.py - the MINIMUM VIABLE MEASUREMENT for fntn.

NON-EVIDENTIARY. This script is deliberately crude. It exists to BOUND the
answer to one question - is there any edge in insider open-market purchases at
h=5 after this project's own registered costs - at the lowest possible cost,
before another register row is opened.

It MUST NOT be cited as a calibration, may not register a parameter, and no
§13 row may take a reading from it. Its output carries that stamp.

The protocol below was fixed on 19 September 2026 BEFORE any price data was
fetched and before any result existed. Changing it after seeing a result is
the failure this file is written against.

Usage:
    export SEC_CONTACT="Your Name your@email.com"
    python3 mvm.py --provider stooq --out results/
    python3 mvm.py --provider eodhd --eodhd-key $EODHD_KEY --out results/
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from typing import Iterable, Sequence

# ----------------------------------------------------------------------------
# PRE-REGISTERED PROTOCOL. Fixed 2026-09-19. Do not edit after a result exists.
# ----------------------------------------------------------------------------

PROTOCOL = {
    "registered_on": "2026-09-19",
    "span_start": "2023-01-01",          # = archive_opens, registered
    "span_end": "2026-08-27",            # = delisting register's span end
    "family": "insider_dealing",          # the family retired by 0c
    "event": "Form 4, transaction code P (open-market purchase), "
             "by an officer or director, non-derivative table only",
    "entry": "open of the first session after the FILING date (not the "
             "transaction date). §4.3: fills at the open of the session "
             "after signal completion.",
    "horizon_sessions": 5,               # §4.1 admissible; §0.9's breadth cell
    "exit": "open, h sessions after entry",
    "min_share_price_usd": 10.42,        # achievability criterion 3, at row 29 = 10bp
    "min_median_notional_usd": 40_312.0, # achievability criterion 4
    "round_trip_cost_bps": 15.70,        # delta_min = 8.7 (row 29 bound) + 7.0 (spread)
    "cost_note": "FLAT. Excludes market impact by construction (§13 row 37 "
                 "is BLOCKED and has never had a column). The true cost is "
                 "higher and this is stated rather than modelled.",
    "materiality_filter_pct_mktcap": None,  # None = OFF for the primary run.
                                            # 0.1 reproduces the FGR panel that
                                            # separates 462bp from 165bp (§0.5).
    "gates": "NONE. No funnel, no gate stack, no ledger, no sizing. "
             "Deliberately. This measures the raw event, not the system.",
    "primary_statistic": "mean net 5-session return per event, in bp, "
                         "with a 95% CI and the count",
    "decision_rule": (
        "Fixed before the result. Let r_net be the mean net return in bp and "
        "L the lower 95% bound.\n"
        "  (a) L <= 0        -> NO EDGE DEMONSTRATED. The programme's premise "
        "is not supported and no register row can rescue it.\n"
        "  (b) 0 < L < 13.9  -> EDGE BELOW THE PASSIVE HURDLE. Statistically "
        "present, economically dominated by a tracker. Stop.\n"
        "  (c) L >= 13.9     -> CLEARS THE PASSIVE HURDLE. Every blocked §13 "
        "row acquires a price and the register can be ordered by consequence.\n"
        "  (d) L >= 43.7     -> CLEARS THE FULL HURDLE including engineering "
        "time. Only here is the programme worth its own cost."
    ),
    "hurdles_bps_at_h5": {"cash_4pct": 7.9, "tracker_7pct": 13.9,
                          "cash_plus_time": 37.7, "tracker_plus_time": 43.7},
}

SEC_RATE_LIMIT_S = 0.12          # SEC fair-access: <= 10 req/s. We use ~8.
USER_AGENT_ENV = "SEC_CONTACT"   # the string that gates step 4 and this run


# ----------------------------------------------------------------------------
# Fetch helpers
# ----------------------------------------------------------------------------

def _contact() -> str:
    c = os.environ.get(USER_AGENT_ENV, "").strip()
    if not c:
        sys.exit(
            f"{USER_AGENT_ENV} is unset. SEC fair-access requires a contact "
            f"string.\n  export {USER_AGENT_ENV}=\"Your Name your@email.com\""
        )
    return c


def _get(url: str, *, binary: bool = False, tries: int = 3) -> bytes | str:
    req = urllib.request.Request(url, headers={
        "User-Agent": _contact(),
        "Accept-Encoding": "gzip, deflate",
        "Host": urllib.parse.urlparse(url).netloc,
    })
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding", "")
                if "gzip" in enc:
                    import gzip
                    raw = gzip.decompress(raw)
                elif "deflate" in enc:
                    import zlib
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                time.sleep(SEC_RATE_LIMIT_S)
                return raw if binary else raw.decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after {tries}: {url}: {last}")


# ----------------------------------------------------------------------------
# Step 1. The Form 4 population, from EDGAR full-index
# ----------------------------------------------------------------------------

@dataclasses.dataclass
class Filing:
    cik: str
    company: str
    date_filed: dt.date
    path: str


def quarters(start: dt.date, end: dt.date) -> Iterable[tuple[int, int]]:
    y, q = start.year, (start.month - 1) // 3 + 1
    while (y, q) <= (end.year, (end.month - 1) // 3 + 1):
        yield y, q
        q += 1
        if q == 5:
            y, q = y + 1, 1


def fetch_form4_index(start: dt.date, end: dt.date, cache: pathlib.Path) -> list[Filing]:
    """Every Form 4 in the span, from the quarterly form index."""
    cache.mkdir(parents=True, exist_ok=True)
    out: list[Filing] = []
    for y, q in quarters(start, end):
        f = cache / f"form_{y}Q{q}.idx"
        if not f.exists():
            url = f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx"
            print(f"  fetching {y} Q{q} form index ...", flush=True)
            f.write_text(_get(url))
        for line in f.read_text(errors="replace").splitlines():
            if not line.startswith("4 "):
                continue
            # fixed-width: Form Type(12) Company(62) CIK(12) Date(12) File Name
            form = line[0:12].strip()
            if form != "4":
                continue
            company = line[12:74].strip()
            cik = line[74:86].strip()
            date_s = line[86:98].strip()
            path = line[98:].strip()
            try:
                d = dt.date.fromisoformat(date_s)
            except ValueError:
                continue
            if start <= d <= end:
                out.append(Filing(cik, company, d, path))
    print(f"  Form 4 filings in span: {len(out):,}")
    return out


# ----------------------------------------------------------------------------
# Step 2. Parse each Form 4 for open-market purchases
# ----------------------------------------------------------------------------

TX_RE = re.compile(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", re.S)
VAL_RE = {
    "code":   re.compile(r"<transactionCode>\s*([^<]+?)\s*</transactionCode>"),
    "shares": re.compile(r"<transactionShares>.*?<value>\s*([\d.]+)\s*</value>", re.S),
    "price":  re.compile(r"<transactionPricePerShare>.*?<value>\s*([\d.]+)\s*</value>", re.S),
    "acq":    re.compile(r"<transactionAcquiredDisposedCode>.*?<value>\s*([ADad])\s*</value>", re.S),
}
ROLE_RE = re.compile(r"<(isDirector|isOfficer)>\s*(1|true)\s*</\1>", re.I)
TICKER_RE = re.compile(r"<issuerTradingSymbol>\s*([^<]+?)\s*</issuerTradingSymbol>")


@dataclasses.dataclass
class Purchase:
    cik: str
    ticker: str
    date_filed: dt.date
    shares: float
    price: float
    notional: float


def parse_form4(doc: str, f: Filing) -> Purchase | None:
    if not ROLE_RE.search(doc):
        return None                                  # criterion: officer/director only
    tk = TICKER_RE.search(doc)
    if not tk:
        return None
    ticker = tk.group(1).strip().upper()
    if not ticker or ticker in {"N/A", "NONE"}:
        return None
    shares = price = 0.0
    for block in TX_RE.findall(doc):
        code = VAL_RE["code"].search(block)
        acq = VAL_RE["acq"].search(block)
        if not code or code.group(1).strip() != "P":
            continue                                 # P = open-market purchase
        if not acq or acq.group(1).upper() != "A":
            continue                                 # acquired, not disposed
        s = VAL_RE["shares"].search(block)
        p = VAL_RE["price"].search(block)
        if not s or not p:
            continue
        sv, pv = float(s.group(1)), float(p.group(1))
        if pv <= 0:
            continue
        shares += sv
        price = pv if price == 0 else price
    if shares <= 0 or price <= 0:
        return None
    return Purchase(f.cik, ticker, f.date_filed, shares, price, shares * price)


def collect_purchases(filings: Sequence[Filing], cache: pathlib.Path,
                      limit: int | None) -> list[Purchase]:
    cache.mkdir(parents=True, exist_ok=True)
    out: list[Purchase] = []
    todo = filings[:limit] if limit else filings
    for i, f in enumerate(todo, 1):
        if i % 500 == 0:
            print(f"    parsed {i:,}/{len(todo):,}, purchases {len(out):,}", flush=True)
        key = cache / (f.path.replace("/", "_"))
        if key.exists():
            doc = key.read_text(errors="replace")
        else:
            try:
                doc = _get(f"https://www.sec.gov/Archives/{f.path}")
            except RuntimeError:
                continue
            key.write_text(doc)
        p = parse_form4(doc, f)
        if p:
            out.append(p)
    print(f"  open-market purchase events: {len(out):,}")
    return out


# ----------------------------------------------------------------------------
# Step 3. Prices. Pluggable, because C-12 is undecided.
# ----------------------------------------------------------------------------

class PriceProvider:
    name = "abstract"
    def daily(self, ticker: str) -> dict[dt.date, tuple[float, float]]:
        """-> {date: (open, volume_notional)}. Empty dict if unavailable."""
        raise NotImplementedError


class StooqProvider(PriceProvider):
    """Free. Coverage of delisted names is PARTIAL and UNVERIFIED (C-12)."""
    name = "stooq"
    def daily(self, ticker: str):
        url = (f"https://stooq.com/q/d/l/?s={ticker.lower()}.us"
               f"&d1={PROTOCOL['span_start'].replace('-','')}"
               f"&d2={PROTOCOL['span_end'].replace('-','')}&i=d")
        try:
            txt = _get(url)
        except RuntimeError:
            return {}
        if "<" in txt[:200] or "Date" not in txt[:200]:
            return {}                               # JS notice, not data
        out = {}
        for row in csv.DictReader(io.StringIO(txt)):
            try:
                d = dt.date.fromisoformat(row["Date"])
                o = float(row["Open"]); c = float(row["Close"]); v = float(row["Volume"])
            except (KeyError, ValueError):
                continue
            out[d] = (o, c * v)
        return out


class EodhdProvider(PriceProvider):
    """Subscription. Delisted retention stated on the vendor's own page."""
    name = "eodhd"
    def __init__(self, key: str):
        self.key = key
    def daily(self, ticker: str):
        url = (f"https://eodhd.com/api/eod/{ticker}.US?"
               f"from={PROTOCOL['span_start']}&to={PROTOCOL['span_end']}"
               f"&period=d&fmt=json&api_token={self.key}")
        try:
            data = json.loads(_get(url))
        except (RuntimeError, json.JSONDecodeError):
            return {}
        out = {}
        for row in data:
            try:
                d = dt.date.fromisoformat(row["date"])
                out[d] = (float(row["open"]),
                          float(row["close"]) * float(row["volume"]))
            except (KeyError, ValueError, TypeError):
                continue
        return out


class CsvProvider(PriceProvider):
    """Any local archive: <dir>/<TICKER>.csv with date,open,close,volume."""
    name = "csv"
    def __init__(self, root: str):
        self.root = pathlib.Path(root)
    def daily(self, ticker: str):
        f = self.root / f"{ticker.upper()}.csv"
        if not f.exists():
            return {}
        out = {}
        for row in csv.DictReader(f.open()):
            try:
                d = dt.date.fromisoformat(row["date"][:10])
                out[d] = (float(row["open"]),
                          float(row["close"]) * float(row["volume"]))
            except (KeyError, ValueError):
                continue
        return out


# ----------------------------------------------------------------------------
# Step 4. The measurement
# ----------------------------------------------------------------------------

@dataclasses.dataclass
class Trade:
    ticker: str
    cik: str
    filed: dt.date
    entry_date: dt.date
    entry: float
    exit_date: dt.date
    exit: float
    gross_bps: float
    net_bps: float


def measure(purchases: Sequence[Purchase], prov: PriceProvider,
            delisted_ciks: set[str]) -> tuple[list[Trade], dict]:
    h = PROTOCOL["horizon_sessions"]
    cost = PROTOCOL["round_trip_cost_bps"]
    minpx = PROTOCOL["min_share_price_usd"]
    minliq = PROTOCOL["min_median_notional_usd"]

    by_ticker: dict[str, list[Purchase]] = {}
    for p in purchases:
        by_ticker.setdefault(p.ticker, []).append(p)

    trades: list[Trade] = []
    drop = {"no_prices": 0, "price_floor": 0, "liquidity_floor": 0,
            "no_entry_bar": 0, "truncated_horizon": 0}
    seen_delisted = set()

    for i, (ticker, evs) in enumerate(sorted(by_ticker.items()), 1):
        if i % 200 == 0:
            print(f"    priced {i:,}/{len(by_ticker):,} tickers, "
                  f"trades {len(trades):,}", flush=True)
        series = prov.daily(ticker)
        if not series:
            drop["no_prices"] += len(evs)
            continue
        days = sorted(series)
        idx = {d: k for k, d in enumerate(days)}
        notionals = sorted(v for _, v in series.values())
        med = notionals[len(notionals) // 2] if notionals else 0.0
        if med < minliq:
            drop["liquidity_floor"] += len(evs)
            continue
        for p in evs:
            nxt = next((d for d in days if d > p.date_filed), None)
            if nxt is None:
                drop["no_entry_bar"] += 1
                continue
            k = idx[nxt]
            if k + h >= len(days):
                drop["truncated_horizon"] += 1
                if p.cik in delisted_ciks:
                    seen_delisted.add(p.cik)
                continue
            o_in = series[days[k]][0]
            o_out = series[days[k + h]][0]
            if o_in < minpx:
                drop["price_floor"] += 1
                continue
            if o_in <= 0:
                continue
            gross = (o_out / o_in - 1.0) * 10_000
            trades.append(Trade(ticker, p.cik, p.date_filed, days[k], o_in,
                                days[k + h], o_out, gross, gross - cost))

    stats = _summarise(trades)
    stats["dropped"] = drop
    stats["delisted_events_truncated"] = len(seen_delisted)
    return trades, stats


def _summarise(trades: Sequence[Trade]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0}
    xs = [t.net_bps for t in trades]
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    sd = var ** 0.5
    se = sd / (n ** 0.5)
    lo, hi = mean - 1.959964 * se, mean + 1.959964 * se
    xs_sorted = sorted(xs)
    return {
        "n": n,
        "mean_net_bps": round(mean, 2),
        "sd_bps": round(sd, 1),
        "se_bps": round(se, 2),
        "ci95_bps": [round(lo, 2), round(hi, 2)],
        "median_net_bps": round(xs_sorted[n // 2], 2),
        "share_positive": round(sum(1 for x in xs if x > 0) / n, 4),
        "t_stat": round(mean / se, 2) if se else None,
    }


def verdict(stats: dict) -> str:
    if not stats.get("n"):
        return "NO TRADES. The run produced nothing; the protocol cannot be evaluated."
    lo = stats["ci95_bps"][0]
    H = PROTOCOL["hurdles_bps_at_h5"]
    if lo <= 0:
        return (f"(a) NO EDGE DEMONSTRATED. Lower 95% bound {lo:.1f} bp <= 0. "
                "The programme's premise is not supported by this measurement.")
    if lo < H["tracker_7pct"]:
        return (f"(b) EDGE BELOW THE PASSIVE HURDLE. Lower bound {lo:.1f} bp is "
                f"positive but under the {H['tracker_7pct']} bp a tracker costs.")
    if lo < H["tracker_plus_time"]:
        return (f"(c) CLEARS THE PASSIVE HURDLE at {lo:.1f} bp. Blocked §13 rows "
                "now have a price and the register can be ordered by consequence.")
    return (f"(d) CLEARS THE FULL HURDLE at {lo:.1f} bp, engineering time included.")


def load_delisted(register: pathlib.Path) -> set[str]:
    if not register.exists():
        return set()
    ciks = set()
    with register.open() as f:
        for row in csv.DictReader((l for l in f if not l.startswith("#")),
                                  delimiter="\t"):
            if row.get("form") in {"25", "25-NSE"}:
                ciks.add(row["cik"].lstrip("0"))
    return ciks


# ----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=["stooq", "eodhd", "csv"], default="stooq")
    ap.add_argument("--eodhd-key", default=os.environ.get("EODHD_KEY", ""))
    ap.add_argument("--csv-root", default="prices")
    ap.add_argument("--register", default=os.environ.get("DELISTING_REGISTER",
        str(pathlib.Path(__file__).resolve().parent.parent/"data"/"register.tsv")))
    ap.add_argument("--cache", default=".mvm_cache")
    ap.add_argument("--out", default="results")
    ap.add_argument("--limit-filings", type=int, default=None,
                    help="parse only the first N Form 4s (smoke test)")
    a = ap.parse_args()

    start = dt.date.fromisoformat(PROTOCOL["span_start"])
    end = dt.date.fromisoformat(PROTOCOL["span_end"])
    cache = pathlib.Path(a.cache)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("=" * 74)
    print("MINIMUM VIABLE MEASUREMENT - NON-EVIDENTIARY")
    print("Protocol registered", PROTOCOL["registered_on"], "before any data was fetched")
    print("=" * 74)

    if a.provider == "stooq":
        prov: PriceProvider = StooqProvider()
    elif a.provider == "eodhd":
        if not a.eodhd_key:
            sys.exit("--eodhd-key or EODHD_KEY required for the eodhd provider")
        prov = EodhdProvider(a.eodhd_key)
    else:
        prov = CsvProvider(a.csv_root)
    print(f"price provider: {prov.name}\n")

    print("[1/4] Form 4 index")
    filings = fetch_form4_index(start, end, cache / "index")
    print("\n[2/4] parsing for open-market purchases (code P, officer/director)")
    purchases = collect_purchases(filings, cache / "f4", a.limit_filings)
    print("\n[3/4] delisting register")
    delisted = load_delisted(pathlib.Path(a.register))
    print(f"  distinct delisted CIKs: {len(delisted):,}")
    print("\n[4/4] pricing and measuring")
    trades, stats = measure(purchases, prov, delisted)

    stats["protocol"] = PROTOCOL
    stats["provider"] = prov.name
    stats["run_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    stats["stamp"] = "NON-EVIDENTIARY. May not be cited as a calibration."
    stats["verdict"] = verdict(stats)

    (out / "mvm_stats.json").write_text(json.dumps(stats, indent=2, default=str))
    with (out / "mvm_trades.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "cik", "filed", "entry_date", "entry", "exit_date",
                    "exit", "gross_bps", "net_bps"])
        for t in trades:
            w.writerow([t.ticker, t.cik, t.filed, t.entry_date, f"{t.entry:.4f}",
                        t.exit_date, f"{t.exit:.4f}", f"{t.gross_bps:.2f}",
                        f"{t.net_bps:.2f}"])

    print("\n" + "=" * 74)
    print("RESULT")
    print("=" * 74)
    for k in ("n", "mean_net_bps", "ci95_bps", "sd_bps", "t_stat",
              "median_net_bps", "share_positive"):
        print(f"  {k:<18} {stats.get(k)}")
    print(f"  dropped            {stats.get('dropped')}")
    print("\n  " + stats["verdict"])
    print("\n  NON-EVIDENTIARY. No §13 row may take a reading from this.")
    print(f"\n  written to {out}/")


if __name__ == "__main__":
    main()
