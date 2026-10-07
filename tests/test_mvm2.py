"""Tests for tools/mvm2.py, the amended insider-purchase kill test.

Every fixture is synthetic. Nothing here touches the network, and nothing here
is evidence about any market: the tests establish that the arithmetic is the
arithmetic the amendment describes, which is a different claim from the
amendment being right.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import pathlib
import subprocess
import sys
import zipfile

import pytest

TOOLS = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import mvm2  # noqa: E402

D = dt.date


def sessions(start: D, n: int) -> list[D]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


DAYS = sessions(D(2022, 9, 1), 320)


def write_prices(root: pathlib.Path, ticker: str, opens, closes=None, adj=None, vol=None, days=DAYS):
    closes = closes or opens
    adj = adj or closes
    vol = vol or [1_000_000] * len(days)
    with (root / f"{ticker}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "close", "adj_close", "volume"])
        for d, o, c, a, v in zip(days, opens, closes, adj, vol):
            w.writerow([d, o, c, a, v])


def tsv(header, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


SUB = ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERTRADINGSYMBOL"]
OWN = ["ACCESSION_NUMBER", "RPTOWNER_RELATIONSHIP"]
TRN = ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"]


def make_zip(path: pathlib.Path, sub, own, trn):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("SUBMISSION.tsv", tsv(SUB, sub))
        z.writestr("REPORTINGOWNER.tsv", tsv(OWN, own))
        z.writestr("NONDERIV_TRANS.tsv", tsv(TRN, trn))


def fresh_funnel() -> dict:
    return mvm2.new_funnel()


SPAN = (D(2023, 1, 1), D(2026, 8, 27))


@pytest.fixture
def world(tmp_path):
    z = tmp_path / "2023q1_form345.zip"
    sub = [
        ["a1", "15-MAR-2023", "4", "0000000111", "AAA"],        # director purchase
        ["a2", "15-MAR-2023", "4", "0000000111", "AAA"],        # officer, same issuer-day
        ["a3", "15-MAR-2023", "4/A", "0000000111", "AAA"],      # amendment: never an event
        ["a4", "16-MAR-2023", "4", "0000000222", "BBB"],        # a sale
        ["a5", "16-MAR-2023", "4", "0000000333", "CCC"],        # ten per cent owner only
        ["a6", "16-MAR-2023", "4", "0000000444", "CHEAP"],      # below the price floor
        ["a7", "16-MAR-2023", "4", "0000000555", "AB, ABW"],    # names two securities
        ["a8", "17-MAR-2023", "5", "0000000666", "FFF"],        # Form 5
    ]
    own = [["a1", "Director"], ["a2", "Officer"], ["a3", "Director"], ["a4", "Director"],
           ["a5", "TenPercentOwner"], ["a6", "Director,Officer"], ["a7", "Director"], ["a8", "Director"]]
    trn = [
        ["a1", "13-MAR-2023", "P", "1000", "20.00", "A"],
        ["a1", "14-MAR-2023", "P", "1000", "22.00", "A"],
        ["a2", "14-MAR-2023", "P", "2000", "21.00", "A"],
        ["a2", "14-MAR-2023", "S", "500", "21.00", "D"],
        ["a3", "13-MAR-2023", "P", "9999", "20.00", "A"],
        ["a4", "15-MAR-2023", "S", "100", "50.00", "D"],
        ["a5", "15-MAR-2023", "P", "100", "50.00", "A"],
        ["a6", "15-MAR-2023", "P", "100", "5.00", "A"],
        ["a7", "15-MAR-2023", "P", "100", "50.00", "A"],
        ["a8", "15-MAR-2023", "P", "100", "50.00", "A"],
    ]
    make_zip(z, sub, own, trn)
    return tmp_path, z


def test_the_event_definition_admits_what_it_names_and_nothing_else(world):
    _, z = world
    funnel = fresh_funnel()
    events = mvm2.build_events(mvm2.parse_archive(z, funnel), *SPAN, funnel)
    assert [(e.cik, e.ticker, e.filed) for e in events] == [("111", "AAA", D(2023, 3, 15))]
    e = events[0]
    assert e.n_accessions == 2 and e.shares == 4000
    assert e.notional == pytest.approx(1000 * 20 + 1000 * 22 + 2000 * 21)
    assert e.vwap == pytest.approx(21.0)
    assert e.last_trans == D(2023, 3, 14)
    assert funnel["not_officer_or_director"] == 1      # the ten per cent owner
    assert funnel["price_floor"] == 1 and funnel["bad_ticker"] == 1
    assert funnel["form4"] == 6                        # the 4/A and the Form 5 are not Form 4


@pytest.mark.parametrize("raw,want", [
    ("aapl", "AAPL"), (" BRK.B ", "BRK.B"), ("BRK-B", "BRK.B"), ("BF/B", "BF.B"), ("NYSE: T", "T"),
    ("(NASDAQ:MSFT)", "MSFT"), ("NONE", None), ("NA", None), ("", None), ("AB, ABW", None), ("N/A", None), ("TOOLONGX", None),
])
def test_a_symbol_is_normalised_or_refused_and_never_guessed(raw, want):
    assert mvm2.norm_ticker(raw) == want


def flat_bench(root):
    for b in ("SPY", "IWM"):
        write_prices(root, b, [100.0] * len(DAYS))


def ev(ticker="AAA", cik="111", filed=None, px=50.0, last_trans=None, k=100):
    filed = filed or DAYS[k]
    return mvm2.Event(cik, ticker, filed, 100, 100 * px, last_trans or filed, 1)


def test_entry_is_the_first_open_strictly_after_filing_and_exit_is_h_sessions_on(tmp_path):
    opens = [50.0 + 0.1 * i for i in range(len(DAYS))]
    write_prices(tmp_path, "AAA", opens)
    spy = [100.0 + 0.05 * i for i in range(len(DAYS))]
    write_prices(tmp_path, "SPY", spy)
    write_prices(tmp_path, "IWM", [100.0] * len(DAYS))
    trades, meta = mvm2.measure([ev(px=opens[100])], mvm2.CsvProvider(str(tmp_path)), set())
    (t,) = trades
    assert t.entry_date == DAYS[101] and t.exit_date == DAYS[106]
    assert t.gross_bps == pytest.approx((opens[106] / opens[101] - 1) * 1e4)
    assert t.bench_bps["SPY"] == pytest.approx((spy[106] / spy[101] - 1) * 1e4)
    assert t.bench_bps["IWM"] == pytest.approx(0.0)
    assert t.bucket == "B3 $10m-$100m" and t.cost_mid == 78.7      # 60 x 1,000,000 a day


def test_a_filing_on_a_non_session_enters_at_the_next_session_and_not_before(tmp_path):
    write_prices(tmp_path, "AAA", [50.0] * len(DAYS))
    flat_bench(tmp_path)
    saturday = next(d for d in (DAYS[100] + dt.timedelta(days=i) for i in range(1, 8)) if d.weekday() == 5)
    trades, _ = mvm2.measure([ev(filed=saturday, last_trans=DAYS[100])], mvm2.CsvProvider(str(tmp_path)), set())
    assert trades[0].entry_date == next(d for d in DAYS if d > saturday)


def test_liquidity_is_read_backwards_from_entry_and_never_from_the_whole_span(tmp_path):
    # Illiquid until session 150, liquid after. An event at session 100 must be
    # dropped: only a whole-span median, which looks ahead, would admit it.
    vol = [100] * 150 + [5_000_000] * (len(DAYS) - 150)
    write_prices(tmp_path, "AAA", [50.0] * len(DAYS), vol=vol)
    flat_bench(tmp_path)
    prov = mvm2.CsvProvider(str(tmp_path))
    trades, meta = mvm2.measure([ev(k=100)], prov, set())
    assert trades == [] and meta["dropped"]["liquidity_floor"] == 1
    trades, _ = mvm2.measure([ev(k=250)], prov, set())
    assert len(trades) == 1 and trades[0].bucket == "B2 $100m-$1bn"


def test_a_series_that_is_not_the_security_the_insider_bought_is_dropped(tmp_path):
    write_prices(tmp_path, "AAA", [50.0] * len(DAYS))
    flat_bench(tmp_path)
    prov = mvm2.CsvProvider(str(tmp_path))
    _, meta = mvm2.measure([ev(px=10.5)], prov, set())           # 10.5 / 50 = 0.21
    assert meta["dropped"]["identity_mismatch"] == 1
    _, meta = mvm2.measure([ev(last_trans=D(2019, 1, 2))], prov, set())
    assert meta["dropped"]["identity_unscorable"] == 1
    trades, _ = mvm2.measure([ev(px=26.0)], prov, set())         # 0.52: inside the band
    assert len(trades) == 1


def test_one_position_per_issuer_even_when_the_issuer_files_under_two_symbols(tmp_path):
    for t in ("AAA", "ZZZ"):
        write_prices(tmp_path, t, [50.0] * len(DAYS))
    flat_bench(tmp_path)
    evs = [ev("ZZZ", "111", k=100), ev("AAA", "111", k=102), ev("AAA", "111", k=105), ev("AAA", "111", k=106)]
    trades, meta = mvm2.measure(evs, mvm2.CsvProvider(str(tmp_path)), set())
    # entry 101 holds to 106; entries at 103 and 106 fall inside it; entry at 107 is free.
    assert [(t.ticker, t.entry_date) for t in trades] == [("ZZZ", DAYS[101]), ("AAA", DAYS[107])]
    assert meta["dropped"]["overlap_skipped"] == 2


def test_a_split_and_a_dividend_inside_the_window_are_not_a_return(tmp_path):
    # Two-for-one split effective at session 103 and nothing else happening:
    # nominal prices halve, the adjusted series is flat, and the trade made nothing.
    opens = [50.0] * 103 + [25.0] * (len(DAYS) - 103)
    adj = [25.0] * len(DAYS)
    write_prices(tmp_path, "AAA", opens, closes=opens, adj=adj)
    flat_bench(tmp_path)
    trades, _ = mvm2.measure([ev(px=50.0)], mvm2.CsvProvider(str(tmp_path)), set())
    assert trades[0].gross_bps == pytest.approx(0.0, abs=1e-9)


def test_an_unpriced_event_is_counted_and_marked_when_its_issuer_delisted(tmp_path):
    flat_bench(tmp_path)
    write_prices(tmp_path, "SHORT", [50.0] * 104, days=DAYS[:104])
    evs = [ev("GONE", "999"), ev("GONE2", "998"), ev("SHORT", "997")]
    trades, meta = mvm2.measure(evs, mvm2.CsvProvider(str(tmp_path)), {"999", "997"})
    assert trades == []
    assert meta["dropped"]["no_prices"] == 2 and meta["coverage"]["no_prices_delisted_issuer"] == 1
    assert meta["dropped"]["truncated_horizon"] == 1 and meta["coverage"]["truncated_delisted_issuer"] == 1


def test_an_unanswered_question_is_never_read_as_no_data(tmp_path):
    class Flaky(mvm2.CsvProvider):
        def daily(self, ticker):
            if ticker == "AAA":
                raise mvm2.Transient("429")
            return super().daily(ticker)
    flat_bench(tmp_path)
    _, meta = mvm2.measure([ev()], Flaky(str(tmp_path)), set())
    assert meta["dropped"]["provider_error"] == 1 and meta["dropped"]["no_prices"] == 0
    assert meta["coverage"]["tickers_provider_error"] == 1


def test_the_clustered_interval_matches_an_independent_computation():
    xs = [10.0, 30.0, -20.0, 5.0, 60.0, -15.0, 25.0, 0.0, 40.0, -5.0, 12.0, 18.0, -30.0, 22.0]
    cl = [0, 0, 1, 2, 2, 3, 4, 5, 5, 6, 7, 8, 9, 10]
    s = mvm2.summarise(xs, cl)
    n, mean = len(xs), sum(xs) / len(xs)
    by = {}
    for x, c in zip(xs, cl):
        by.setdefault(c, []).append(x - mean)
    G = len(by)
    se = (G / (G - 1) * sum(sum(v) ** 2 for v in by.values())) ** 0.5 / n
    assert s["clusters"] == 11 and s["mean_bps"] == pytest.approx(mean, abs=0.01)
    assert s["se_bps"] == pytest.approx(se, abs=0.01)
    assert s["ci95_bps"][0] == pytest.approx(mean - 2.2281 * se, abs=0.05)    # t(0.975, 10)
    assert mvm2.summarise(xs[:6], cl[:6])["scorable"] is False               # four clusters: refused


def mk(gross, k, bucket_adv=2e9, spy=0.0, iwm=0.0):
    label, mid, cons = mvm2.bucket_of(bucket_adv)
    d = D(2023, 1, 2) + dt.timedelta(days=31 * k)
    return mvm2.Trade("T", str(k), d, d, d, gross, {"SPY": spy, "IWM": iwm}, bucket_adv, label, mid, cons, 1)


class Keeps(mvm2.PriceProvider):
    name, keeps_delisted = "complete", True


class Omits(mvm2.PriceProvider):
    name, keeps_delisted = "partial", False


FULL = 24 / 1000          # a span over which 24 trades are 1,000 a year: a full book


def spread(centre, n=24, step=2.0):
    return [centre + step * ((i % 5) - 2) for i in range(n)]


@pytest.mark.parametrize("centre,adv,want", [
    (10.0, 2e9, "KILL"),               # under the flat cost
    (60.0, 5e7, "COST-DETERMINED"),    # clears 15.7, not the 78.7 its bucket costs
    (30.0, 2e9, "BEATS A TRACKER"),    # 14.3 net: positive, under 29.8
    (80.0, 2e9, "PAYS FOR ITSELF"),    # 64.3 net
])
def test_each_branch_of_the_decision_rule_fires_where_the_rule_says(centre, adv, want):
    trades = [mk(g, k, adv) for k, g in enumerate(spread(centre))]
    assert mvm2.verdict(trades, Keeps(), span_years=FULL)["verdict"] == want


def test_a_population_too_thin_to_fill_the_book_faces_a_higher_time_hurdle():
    assert mvm2.time_hurdle(806.4) == pytest.approx(15_000 / 504, abs=0.01)
    assert mvm2.time_hurdle(5_000) == pytest.approx(15_000 / 504, abs=0.01)     # a book has sixteen slots
    assert mvm2.time_hurdle(403.2) == pytest.approx(2 * 15_000 / 504, abs=0.01)
    assert mvm2.time_hurdle(0) is None
    trades = [mk(g, k, 2e9) for k, g in enumerate(spread(80.0))]                # 64.3 bp net
    assert mvm2.verdict(trades, Keeps(), span_years=FULL)["verdict"] == "PAYS FOR ITSELF"
    assert mvm2.verdict(trades, Keeps(), span_years=3.65)["verdict"] == "BEATS A TRACKER"   # 6.6 trades a year


def test_an_edge_that_lives_only_where_costs_are_real_is_found_and_named():
    liquid = [mk(g, k, 2e9) for k, g in enumerate(spread(80.0))]
    illiquid = [mk(g, k, 5e6) for k, g in enumerate(spread(80.0)) for _ in range(4)]   # 80 gross, 208.7 cost
    v = mvm2.verdict(liquid + illiquid, Keeps(), span_years=FULL)
    assert v["all_trades"]["T"]["B1-B4"]["branch"] == "COST-DETERMINED"
    assert v["verdict"] == "PAYS FOR ITSELF" and v["deciding_population"] == "B1-B2"


def test_the_worse_benchmark_reading_decides():
    trades = [mk(g, k, 2e9, spy=0.0, iwm=45.0) for k, g in enumerate(spread(50.0))]
    v = mvm2.verdict(trades, Keeps(), span_years=FULL)
    assert v["verdict"] == "KILL"                         # 50 - 45 - 15.7 < 0 against IWM
    assert v["all_trades"]["L_G_bps"] < 0


def test_a_market_that_merely_rose_does_not_pass():
    # 60 bp gross with the market up 60 bp: the 19 September statistic reads a
    # comfortable pass; the amended one reads what it is.
    trades = [mk(g, k, 2e9, spy=60.0, iwm=60.0) for k, g in enumerate(spread(60.0))]
    assert mvm2.registered_s0(trades)["branch_19_sep_rule"] in {"(c)", "(d)"}
    assert mvm2.verdict(trades, Keeps(), FULL)["verdict"] == "KILL"


def test_a_verdict_carried_by_the_tail_takes_the_lower_branch_and_says_so():
    trades = [mk(g, k, 2e9) for k, g in enumerate(spread(10.0, n=40))]
    trades += [mk(15_000.0, 40 + k, 2e9) for k in range(12)]       # twelve 150% weeks
    v = mvm2.verdict(trades, Keeps(), span_years=52 / 1000)
    assert v["all_trades"]["branch"] != "KILL" and v["without_tail"]["branch"] == "KILL"
    assert v["verdict"] == "KILL" and v["tail_dependent"] is True and v["without_tail"]["excluded"] == 12


def test_a_partial_archive_cannot_pass_and_kills_only_where_the_missing_could_not_reverse_it():
    good = [mk(g, k, 2e9) for k, g in enumerate(spread(80.0))]
    bad = [mk(g, k, 2e9) for k, g in enumerate(spread(-5.0))]          # mean net -20.7, n = 24
    assert mvm2.verdict(good, Omits(), FULL)["provisional"] is True
    assert "PROVISIONAL" in mvm2.verdict(good, Omits(), FULL)["text"]
    assert mvm2.verdict(good, Keeps(), FULL)["provisional"] is False
    assert mvm2.verdict(bad, Omits(), FULL)["provisional"] is False     # nothing unpriced: final
    few = mvm2.verdict(bad, Omits(), FULL, unpriced=1)                  # one event would need hundreds of bp
    many = mvm2.verdict(bad, Omits(), FULL, unpriced=24)                # as many again need a few bp each
    assert few["verdict"] == many["verdict"] == "KILL"
    assert few["provisional"] is False and few["survivorship"]["mean_bps_unpriced_events_would_need"] > 230
    assert many["provisional"] is True and many["survivorship"]["mean_bps_unpriced_events_would_need"] < 230
    assert mvm2.verdict(bad, Keeps(), FULL, unpriced=24)["provisional"] is False   # a complete archive kills outright


def test_the_flip_threshold_is_the_arithmetic_it_claims():
    stat = {"scorable": True, "n": 100, "mean_exact": -5.0, "lo_exact": -9.0}
    need = mvm2.flip_threshold(stat, 50)             # pooled mean must reach the half-width, 4.0
    assert (100 * -5.0 + 50 * need) / 150 == pytest.approx(4.0)
    assert mvm2.flip_threshold(stat, 0) is None


def test_a_pass_on_a_complete_archive_is_provisional_if_delisted_losses_could_undo_it():
    good = [mk(g, k, 2e9) for k, g in enumerate(spread(80.0))]          # L(T) about 63 bp over 24 trades
    assert mvm2.verdict(good, Keeps(), FULL, lost_delisted=0)["provisional"] is False
    v = mvm2.verdict(good, Keeps(), FULL, lost_delisted=1)              # one total loss in 25 is 400 bp
    assert v["provisional"] is True and v["survivorship"]["bound_if_every_delisted_loss_were_total_bps"] < 0


def test_below_the_cost_table_a_trade_takes_the_flat_cost_and_no_tiered_one():
    assert mvm2.bucket_of(999_999.0) == ("B5 <$1m", None, None)
    trades = [mk(g, k, 5e5) for k, g in enumerate(spread(400.0))]
    assert mvm2.block(trades, mvm2.TIER_MID)["raw_net"]["n"] == 0
    assert mvm2.block(trades, mvm2.FLAT)["raw_net"]["n"] == len(trades)
    assert mvm2.verdict(trades, Keeps(), FULL)["verdict"] == "UNSCORABLE"   # G passes, T has nothing to score


def test_yahoo_series_are_total_return_with_nominal_closes_recovered(tmp_path):
    day = lambda y, m, d: int(dt.datetime(y, m, d, 14, 30, tzinfo=dt.timezone.utc).timestamp())   # noqa: E731
    res = {"meta": {"gmtoffset": -18000},
           "timestamp": [day(2023, 3, 13), day(2023, 3, 14), day(2023, 3, 15), day(2023, 3, 16)],
           "indicators": {"quote": [{"open": [25.0, 25.5, None, 26.0], "close": [25.2, 25.6, None, 26.5],
                                     "volume": [100, 200, None, 300]}],
                          "adjclose": [{"adjclose": [24.948, 25.344, None, 26.5]}]},
           "events": {"splits": {"x": {"date": day(2023, 3, 15), "numerator": 2, "denominator": 1}}}}
    (tmp_path / "AAA-B.json").write_text(json.dumps(res))
    (tmp_path / "GONE.json").write_text("null")
    prov = mvm2.YahooProvider(tmp_path)
    s = prov.daily("AAA.B")
    assert s.dates == [D(2023, 3, 13), D(2023, 3, 14), D(2023, 3, 16)]
    assert s.nominal == pytest.approx([50.4, 51.2, 26.5])          # pre-split closes doubled back
    assert s.tr_open[0] == pytest.approx(25.0 * 24.948 / 25.2)
    assert s.notional == pytest.approx([25.2 * 100, 25.6 * 200, 26.5 * 300])
    assert prov.daily("GONE") is None


def test_the_smoke_run_writes_coverage_and_no_return(world):
    root, z = world
    px = root / "px"
    px.mkdir()
    write_prices(px, "AAA", [21.0] * len(DAYS))
    flat_bench(px)
    out = root / "out"
    reg = pathlib.Path(__file__).resolve().parent.parent / "archive" / "delistings" / "register.tsv"
    cmd = [sys.executable, str(TOOLS / "mvm2.py"), "--provider", "csv", "--csv-root", str(px),
           "--archives", str(root), "--register", str(reg), "--out", str(out)]
    r = subprocess.run(cmd + ["--smoke", "5"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (out / "coverage.json").exists() and not (out / "killtest_stats.json").exists()
    assert "bps" not in r.stdout and "trades    1" in r.stdout
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    stats = json.loads((out / "killtest_stats.json").read_text())
    assert stats["trades"] == 1 and stats["verdict"]["verdict"] == "UNSCORABLE"
    assert stats["protocol_hash"] == mvm2.protocol_hash()


def test_the_amendment_leaves_the_registered_protocol_as_it_was():
    import mvm
    assert mvm.PROTOCOL["registered_on"] == "2026-09-19"
    u = mvm2.PROTOCOL2["unchanged"]
    assert (u["span_start"], u["span_end"], u["horizon_sessions"]) == ("2023-01-01", "2026-08-27", 5)
    assert (u["min_share_price_usd"], u["min_median_notional_usd"], u["flat_round_trip_cost_bps"]) == (10.42, 40_312.0, 15.70)
    assert mvm2.PROTOCOL2["time_hurdle_bps_at_full_book"] == pytest.approx((22_000 - 7_000) / 504, abs=0.05)
    assert mvm2.PROTOCOL2["trades_per_year_at_full_book"] == pytest.approx(16 * 252 / 5)
    assert [t[2] for t in mvm2.PROTOCOL2["A3_cost_tiers_bps"]] == [15.7, 28.7, 78.7, 208.7]


def test_a_row_whose_columns_cannot_be_trusted_is_counted_and_never_read(tmp_path):
    z = tmp_path / "2023q1_form345.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("SUBMISSION.tsv", "\ufeff" + "\t".join(SUB) + "\n"
                   "a1\t15-MAR-2023\t4\t0000000111\tAAA\n"
                   "a2\t15-MAR-2023\t4\t0000000222\tBBB INC\tBBB\n"      # a stray tab: six fields
                   "a3\t15-MAR-2023\n")                                       # cut short
        f.writestr("REPORTINGOWNER.tsv", tsv(OWN, [["a1", "Director"], ["a2", "Director"]]))
        f.writestr("NONDERIV_TRANS.tsv", tsv(TRN, [["a1", "14-MAR-2023", "P", "100", "20.00", "A"],
                                                   ["a2", "14-MAR-2023", "P", "100", "20.00", "A"]]))
    funnel = fresh_funnel()
    recs = mvm2.parse_archive(z, funnel)
    assert [r["acc"] for r in recs] == ["a1"] and funnel["malformed_rows"] == 2


def test_a_transaction_dated_after_its_own_filing_anchors_nothing(tmp_path):
    write_prices(tmp_path, "AAA", [50.0] * len(DAYS))
    flat_bench(tmp_path)
    _, meta = mvm2.measure([ev(k=100, last_trans=DAYS[104])], mvm2.CsvProvider(str(tmp_path)), set())
    assert meta["dropped"]["identity_unscorable"] == 1


def test_nothing_after_the_exit_open_and_nothing_on_entry_day_but_its_open_reaches_a_trade(tmp_path):
    import random
    rng = random.Random(7)
    opens = [50.0 + rng.uniform(-1, 1) for _ in DAYS]
    closes = [o + rng.uniform(-0.5, 0.5) for o in opens]
    vol = [rng.randint(200_000, 900_000) for _ in DAYS]
    a = tmp_path / "a"; b = tmp_path / "b"
    a.mkdir(); b.mkdir()
    for root in (a, b):
        flat_bench(root)
    write_prices(a, "AAA", opens, closes=closes, vol=vol)
    c2, v2, o2 = closes[:], vol[:], opens[:]
    c2[101] *= 3; v2[101] *= 50                      # entry day: close and volume are not yet known at the open
    for i in range(107, len(DAYS)):                  # everything after the exit open
        o2[i] *= 2; c2[i] *= 2; v2[i] *= 100
    write_prices(b, "AAA", o2, closes=c2, vol=v2)
    e = ev(px=closes[100], k=100)
    ta, _ = mvm2.measure([e], mvm2.CsvProvider(str(a)), set())
    tb, _ = mvm2.measure([e], mvm2.CsvProvider(str(b)), set())
    assert len(ta) == 1 and dataclasses_equal(ta[0], tb[0])


def dataclasses_equal(x, y) -> bool:
    import dataclasses
    return dataclasses.asdict(x) == dataclasses.asdict(y)


def test_a_hole_inside_the_span_refuses_and_a_short_end_does_not():
    qs = mvm2.quarters(*SPAN)
    assert qs[0] == "2023q1" and qs[-1] == "2026q3" and len(qs) == 15
    mvm2.check_contiguous(qs, *SPAN)
    mvm2.check_contiguous(qs[:-2], *SPAN)                       # the span simply ends earlier
    with pytest.raises(SystemExit):
        mvm2.check_contiguous(qs[:3] + qs[4:], *SPAN)
    with pytest.raises(SystemExit):
        mvm2.check_contiguous(qs[1:], *SPAN)
    with pytest.raises(SystemExit):
        mvm2.check_contiguous([], *SPAN)


def planted_world(root: pathlib.Path, drift_bps: float):
    """Forty issuers, one purchase a fortnight each for a year, every one
    followed by the same five-session drift; the benchmarks flat."""
    days = sessions(D(2022, 9, 1), 420)
    px = root / "px"; px.mkdir()
    for b in ("SPY", "IWM"):
        write_prices(px, b, [100.0] * len(days), days=days)
    sub, own, trn = [], [], []
    fmt = lambda d: d.strftime("%d-%b-%Y").upper()              # noqa: E731
    for i in range(40):
        tk = "T" + "ABCDEFGHIJ"[i // 10] + "ABCDEFGHIJ"[i % 10]
        opens = [40.0] * len(days)
        for n, k in enumerate(range(100, 360, 10)):
            acc = f"x{i}-{n}"
            sub.append([acc, fmt(days[k]), "4", f"{1000 + i:010d}", tk])
            own.append([acc, "Director"])
            trn.append([acc, fmt(days[k]), "P", "500", f"{opens[k]:.2f}", "A"])
            for j in range(k + 2, len(days)):                   # the drift lands between the entry and exit opens
                opens[j] *= 1 + drift_bps / 1e4 if j == k + 2 else 1
            for j in range(k + 3, len(days)):
                opens[j] = opens[k + 2]
        write_prices(px, tk, opens, vol=[60_000_000] * len(days), days=days)   # USD 2.4bn a day: B1
    for q in mvm2.quarters(*SPAN):
        make_zip(root / f"{q}_form345.zip", sub if q == "2023q1" else [], own if q == "2023q1" else [],
                 trn if q == "2023q1" else [])
    return px


@pytest.mark.parametrize("drift,want", [(0.0, "KILL"), (120.0, "PAYS FOR ITSELF")])
def test_end_to_end_a_planted_effect_is_found_and_a_planted_null_is_killed(tmp_path, drift, want):
    px = planted_world(tmp_path, drift)
    reg = pathlib.Path(__file__).resolve().parent.parent / "archive" / "delistings" / "register.tsv"
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(TOOLS / "mvm2.py"), "--provider", "csv", "--csv-root", str(px),
                        "--csv-keeps-delisted", "--archives", str(tmp_path), "--register", str(reg),
                        "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    stats = json.loads((out / "killtest_stats.json").read_text())
    g = stats["G_all_trades_flat_cost"]["abnormal_net_vs_SPY"]
    assert stats["trades"] == 40 * 26 and g["mean_bps"] == pytest.approx(drift - 15.7, abs=0.05)
    assert stats["verdict"]["verdict"] == want, stats["verdict"]["text"]
    assert "Verdict" in (out / "killtest_report.md").read_text()


def test_the_run_refuses_when_the_provider_leaves_too_much_unanswered(world, monkeypatch, tmp_path):
    root, z = world
    reg = pathlib.Path(__file__).resolve().parent.parent / "archive" / "delistings" / "register.tsv"

    class Deaf(mvm2.CsvProvider):
        def daily(self, ticker):
            if ticker in ("SPY", "IWM"):
                return mvm2.Series([D(2023, 1, 3)], [1.0], [1.0], [1.0])
            raise mvm2.Transient("429")
    monkeypatch.setattr(mvm2, "CsvProvider", Deaf)
    monkeypatch.setattr(sys, "argv", ["mvm2.py", "--provider", "csv", "--archives", str(root),
                                      "--register", str(reg), "--out", str(tmp_path / "o")])
    # the fixture holds only 2023q1, which is a short end and not a hole
    with pytest.raises(SystemExit) as e:
        mvm2.main()
    assert "provider_unreliable" in str(e.value)
    assert not (tmp_path / "o" / "killtest_stats.json").exists()


def test_the_register_has_no_default_and_an_empty_one_refuses(tmp_path):
    r = subprocess.run([sys.executable, str(TOOLS / "mvm2.py"), "--provider", "csv"], capture_output=True, text=True)
    assert r.returncode != 0 and "--register" in r.stderr
    empty = tmp_path / "r.tsv"
    empty.write_text("form\tcik\n15-12G\t123\n")
    with pytest.raises(SystemExit) as e:
        mvm2.load_delisted(empty)
    assert "delisting_register_empty" in str(e.value)
