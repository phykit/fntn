"""Self-test for the credit-drift plumbing, on a SYNTHETIC panel. No network, no real data.

Why this exists: the reconstruction of stock returns is derived algebra that the real inputs can
only validate indirectly (against Mom12m). Here the truth is known. A synthetic monthly stock panel
is built with listing dates, delistings, gaps and missing returns; the three signals are computed
from it by the publisher's definitions; and `cdlib.reconstruct` must give back every return except
each firm's last. The same panel carries synthetic bonds so the issuer-month collapse and the
bond-to-stock linkage are checked against brute-force loops.

Run: python tools/credit_drift/selftest.py        (exits non-zero on any failure)
"""
import io
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdlib  # noqa: E402

START = 1995 * 12          # January 1995
END = 2024 * 12 + 11       # December 2024, the synthetic stock file's final month
BOND_END = END + 6         # the bond panel runs past the stock file, as the published one does


def make_stocks(n_firms=600, seed=7):
    """Synthetic firm-month returns. Returns {permno: {mi: return or None}} (None = missing return)."""
    rng = np.random.default_rng(seed)
    firms = {}
    for i in range(n_firms):
        permno = 10000 + i
        a = int(rng.integers(START, END - 3))
        kind = rng.random()
        if kind < 0.45:
            b = END                                   # alive at the panel's end
        elif kind < 0.55:
            b = min(END, a + int(rng.integers(1, 11)))  # short-lived: fewer than 12 listed months
        else:
            b = min(END, a + int(rng.integers(12, 240)))
        months = list(range(a, b + 1))
        if rng.random() < 0.08 and len(months) > 40:   # a gap in the listing
            g0 = int(rng.integers(15, len(months) - 15))
            g1 = g0 + int(rng.integers(1, 9))
            months = months[:g0] + months[g1:]
        rets = {}
        for j, m in enumerate(months):
            x = float(np.clip(rng.normal(0.01, 0.13), -0.97, 3.0))
            if j == 0 or rng.random() < 0.004:
                x = None                               # first month, or a sporadic missing return
            if rng.random() < 0.002:
                x = -0.995                             # a near-total loss, to reach the guard
            rets[m] = x
        firms[permno] = rets
    return firms


def make_signals(firms):
    """The three signals by the publisher's definitions. Returns {name: DataFrame permno, yyyymm, name}."""
    rows = {n: [] for n in cdlib.SIGNALS}
    for permno, rets in firms.items():
        r0 = {m: (0.0 if v is None else v) for m, v in rets.items()}
        for m in rets:
            if (m - 11) in r0:
                rows["MomSeasonShort"].append((permno, m, r0[m - 11]))
            if all((m - k) in r0 for k in range(1, 6)):
                rows["Mom6m"].append((permno, m, float(np.prod([1 + r0[m - k] for k in range(1, 6)]) - 1)))
            if all((m - k) in r0 for k in range(1, 12)):
                rows["Mom12m"].append((permno, m, float(np.prod([1 + r0[m - k] for k in range(1, 12)]) - 1)))
    out = {}
    for n, rr in rows.items():
        d = pd.DataFrame(rr, columns=["permno", "mi", n])
        d["yyyymm"] = cdlib.yyyymm_from_mi(d["mi"].to_numpy())
        out[n] = d[["permno", "yyyymm", n]]
    return out


def make_bonds(firms, seed=11, effect=0.0, first=2002 * 12 + 7):
    """Synthetic bond-month panel in the published file's shape, and (optionally) a planted effect.

    If `effect` is non-zero the firms' returns are MODIFIED IN PLACE so that the stock return in
    month t+1 rises by `effect` times the issuer's standardised credit return in month t. The caller
    must therefore build the signals after this call.
    """
    rng = np.random.default_rng(seed)
    rows = []
    issuers = [p for p in firms if rng.random() < 0.6]
    for permno in issuers:
        months = sorted(firms[permno])
        hy = rng.random() < 0.6
        n_b = int(rng.integers(1, 5))
        common = {}
        for b in range(n_b):
            cusip = f"{permno:06d}{b:03d}"
            cs = float(rng.uniform(0.01, 0.09))
            mcap = float(rng.uniform(1e5, 1e6))
            b_start = months[0] + int(rng.integers(0, 6))
            b_end = months[-1] + int(rng.integers(0, 5))      # bonds can outlive the listing
            for m in range(max(b_start, first), min(b_end, BOND_END) + 1):
                if rng.random() < 0.03:
                    continue                                   # an untraded month
                if m not in common:
                    common[m] = float(rng.normal(0.0, 0.02))
                tret = round(float(rng.normal(0.003, 0.01)), 4)
                x = common[m] + float(rng.normal(0.0, 0.004))
                cs_new = max(0.001, cs - 0.2 * x + float(rng.normal(0, 0.001)))
                u = rng.random()
                rating = (11 if hy else 1) if u < 0.9 else (np.nan if u < 0.95 else (1 if hy else 11))
                rows.append({"cusip": cusip, "date": pd.Timestamp(year=m // 12, month=m % 12 + 1, day=1) + pd.offsets.MonthEnd(0),
                             "permno": float(permno) if rng.random() > 0.01 else np.nan,
                             "country": "USA" if rng.random() > 0.02 else "CAN",
                             "ret_type": "standard" if rng.random() > 0.03 else "trad_in_def",
                             "spc_rat": rating, "ret_vw": (tret + x) if rng.random() > 0.01 else np.nan,
                             "tret": tret, "mcap_s": mcap, "cs": cs_new if rng.random() > 0.02 else np.nan})
                cs = cs_new
                mcap *= 1 + x
        if effect:
            for m, c in common.items():
                if (m + 1) in firms[permno] and firms[permno][m + 1] is not None:
                    firms[permno][m + 1] = float(np.clip(firms[permno][m + 1] + effect * c / 0.02, -0.97, 3.0))
    # bonds of issuers with no listed stock at all
    for j in range(60):
        cusip = f"99{j:04d}000"
        for m in range(first, END + 1, 1):
            if rng.random() < 0.5:
                continue
            rows.append({"cusip": cusip, "date": pd.Timestamp(year=m // 12, month=m % 12 + 1, day=1) + pd.offsets.MonthEnd(0),
                         "permno": np.nan if j % 2 else float(90000 + j), "country": "USA", "ret_type": "standard", "spc_rat": 11,
                         "ret_vw": float(rng.normal(0.005, 0.03)), "tret": 0.003, "mcap_s": 5e5, "cs": 0.06})
    return pd.DataFrame(rows)


def check(cond, msg, fails):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def main():
    fails = []
    firms = make_stocks()
    bonds = make_bonds(firms)
    sig = make_signals(firms)

    # 1. CSV round trip through the parser
    for n in cdlib.SIGNALS:
        buf = io.BytesIO()
        sig[n].to_csv(buf, index=False)
        d, n_null = cdlib.parse_signal(n, buf.getvalue())
        check(len(d) == len(sig[n]) and n_null == 0, f"parse_signal round trip: {n}, {len(d):,} rows", fails)
    try:
        cdlib.parse_signal("Mom6m", b"permno,yyyymm,Other\n1,200001,0.1\n")
        check(False, "parse_signal refuses unexpected columns", fails)
    except cdlib.Refusal:
        check(True, "parse_signal refuses unexpected columns", fails)

    # 2. reconstruction against the truth
    stk = cdlib.reconstruct(sig)
    K, r, origin = stk["key"], stk["r"], stk["origin"]
    rec = {int(k): float(v) for k, v in zip(K, r) if np.isfinite(v)}
    n_truth = n_hit = n_final = n_final_rec = n_other_missing = 0
    max_err = 0.0
    for permno, rets in firms.items():
        months = sorted(rets)
        last_row_expected = None
        r0 = {m: (0.0 if v is None else v) for m, v in rets.items()}
        sig_months = [m for m in months if (m - 11) in r0 or all((m - k) in r0 for k in range(1, 6))]
        if sig_months:
            last_row_expected = max(sig_months)
        for m in months:
            key = permno * cdlib.KEY_BASE + m
            n_truth += 1
            if m == months[-1]:
                n_final += 1
                n_final_rec += key in rec
                continue
            if key in rec:
                n_hit += 1
                max_err = max(max_err, abs(rec[key] - r0[m]))
            else:
                n_other_missing += 1
        if last_row_expected is not None:
            got = stk["last_row"].get(permno)
            if got != last_row_expected:
                fails.append(f"last_row mismatch for {permno}")
    truth_keys = {p * cdlib.KEY_BASE + m for p, rets in firms.items() for m in rets}
    check(all(k in truth_keys for k in rec), "no return is recovered for a month the firm was not listed", fails)
    check(max_err < 1e-9, f"recovered returns equal the truth: {n_hit:,} months, max abs error {max_err:.2e}", fails)
    check(n_final_rec == 0, f"no firm's final month is recovered ({n_final:,} final months)", fails)
    share = n_hit / (n_truth - n_final)
    check(share > 0.93, f"share of non-final months recovered: {share:.4f} ({n_other_missing:,} unrecovered: short histories, gaps, guard)", fails)
    check(stk["panel_end"] == END, "panel end is the last signal month", fails)
    print("     passes:", stk["passes"], "| origin counts:", dict(zip(*np.unique(origin, return_counts=True))))

    # 3. validations
    v1 = cdlib.validate_mom12m(stk)
    s_all = cdlib.error_summary(v1["err"], 1e-3)
    s_roll = cdlib.error_summary(v1["err"][v1["rolled"]], 1e-3)
    check(s_all["n"] > 0 and s_all["max"] < 1e-8, f"Mom12m rebuilt, all comparisons: n {s_all['n']:,}, max {s_all['max']:.2e}", fails)
    check(s_roll["n"] > 0 and s_roll["max"] < 1e-8, f"Mom12m rebuilt, rolled comparisons: n {s_roll['n']:,}, max {s_roll['max']:.2e}", fails)
    v2 = cdlib.error_summary(cdlib.validate_roll_on_seeds(stk)["err"], 1e-3)
    check(v2["n"] > 0 and v2["max"] < 1e-8, f"roll-forward formula against seeds: n {v2['n']:,}, max {v2['max']:.2e}", fails)

    # 4. issuer-month collapse against a brute-force loop
    im = cdlib.issuer_months(bonds)
    b = bonds.copy()
    b["mi"] = cdlib.mi_from_dates(b["date"])
    cs_at = {(c, m): v for c, m, v in zip(b["cusip"], b["mi"], b["cs"])}
    acc = {}
    for row in b.itertuples(index=False):
        if row.country != "USA" or pd.isna(row.permno) or pd.isna(row.ret_vw) or pd.isna(row.tret) or not (row.mcap_s > 0) or row.spc_rat not in (1, 11):
            continue
        a = acc.setdefault((int(row.permno), int(row.mi)), [0.0, 0.0, 0.0, 0, 0.0, 0.0])
        a[0] += row.mcap_s; a[1] += row.mcap_s * (row.ret_vw - row.tret); a[2] += row.mcap_s * (row.spc_rat == 11); a[3] += 1
        prev = cs_at.get((row.cusip, row.mi - 1))
        if prev is not None and not pd.isna(prev) and not pd.isna(row.cs):
            a[4] += row.mcap_s; a[5] += row.mcap_s * (row.cs - prev)
    check(len(im) == len(acc), f"issuer-months: {len(im):,} rows, same as brute force", fails)
    worst = 0.0
    for row in im.itertuples(index=False):
        a = acc[(int(row.permno), int(row.mi))]
        worst = max(worst, abs(row.CR - a[1] / a[0]), abs(row.hy_share - a[2] / a[0]), abs(row.n_bonds - a[3]))
        if a[4] > 0:
            worst = max(worst, abs(row.DCS - a[5] / a[4]))
        elif not np.isnan(row.DCS):
            worst = 1.0
    check(worst < 1e-10, f"issuer-month CR, hy_share, n_bonds and DCS equal brute force (max abs diff {worst:.2e})", fails)

    # 5. linkage reasons against a brute-force classification
    lk = cdlib.link(im, stk)
    # listed at t, rebuilt here from the signal frames themselves and not taken from cdlib
    listed = set()
    for n in cdlib.SIGNALS:
        listed |= set((sig[n]["permno"].to_numpy() * cdlib.KEY_BASE + cdlib.mi_from_yyyymm(sig[n]["yyyymm"].to_numpy())).tolist())
    first_listed, last_row = {}, {}
    for k in listed:
        p_, m_ = divmod(k, cdlib.KEY_BASE)
        first_listed[p_] = min(first_listed.get(p_, m_), m_)
        last_row[p_] = max(last_row.get(p_, m_), m_)
    bad = 0
    for row in lk.itertuples(index=False):
        p, t = int(row.permno), int(row.mi)
        kt = p * cdlib.KEY_BASE + t
        if p not in last_row and p not in first_listed:
            exp = "permno_not_in_stock_file"
        elif kt not in listed and t > END:
            exp = "after_stock_file_end"
        elif kt not in listed:
            exp = "not_listed_yet_at_t" if t < first_listed.get(p, 10**9) else ("delisted_before_t" if t > last_row.get(p, -1) else "gap_at_t")
        elif (kt + 1) in rec:
            exp = "ok"
        elif t == last_row.get(p):
            exp = "t_is_final_month" if t < END else "t_is_panel_end"
        elif t + 1 == last_row.get(p):
            exp = "t1_is_final_month_lost" if t + 1 < END else "t1_is_panel_end"
        else:
            exp = "t1_unrecovered_other"
        if exp != row.reason or (exp == "ok") != bool(np.isfinite(row.r_t1)) or (exp == "ok" and abs(row.r_t1 - rec[kt + 1]) > 0):
            bad += 1
    counts = lk["reason"].value_counts().to_dict()
    check(bad == 0, f"linkage reasons equal brute force on {len(lk):,} issuer-months", fails)
    check(set(counts) == set(cdlib.MISS_REASONS), f"every reason is reached: {counts}", fails)

    # 6. units
    check(cdlib.unit_of(bonds["ret_vw"].dropna(), "bond")[0] == "decimal", "unit rule: synthetic bond returns are decimal", fails)
    check(cdlib.unit_of(bonds["ret_vw"].dropna() * 100, "bond")[0] == "percent", "unit rule: the same in per cent is seen as per cent", fails)
    check(cdlib.unit_of(sig["MomSeasonShort"]["MomSeasonShort"], "stock")[0] == "decimal", "unit rule: synthetic stock returns are decimal", fails)

    print(f"\nselftest: {'PASSED' if not fails else 'FAILED'} ({len(fails)} failure(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
