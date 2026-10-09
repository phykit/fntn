"""The frozen credit-drift test (hypothesis H1). NON-EVIDENTIARY side test, outside the FNTN funnel.

This file implements tools/credit_drift/PREREG.md and nothing else. The specification governs: where
the two disagree the specification is right and this file is wrong, and the disagreement is a
deviation to be reported, not a licence to re-read the rule.

Order of work, and why it is this order: every refusal is decided BEFORE any outcome is computed
(input hashes, units, the reconstruction's validation), so a refusal cannot be influenced by what
the answer would have been. Statistics are computed in full and written once at the end; nothing
is printed by level of the signal until the verdict is fixed by the frozen rules.

It publishes derived statistics only: no row of either input and no reconstructed stock return is
printed or written.
"""
import argparse
import json
import math
import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdlib  # noqa: E402

# ----- frozen parameters (PREREG.md section numbers in brackets) --------------------------------
EXPECTED = {            # [2] input pins from probe run 2; a mismatch is a refusal
    "panel_zip_sha256": "bfcd509a923d34950318732171f571dbd202b05778048ce67121e5cf53c1e96f",
    "panel_member": "main_panel_2026.parquet",
    "panel_member_sha256": "64bf67fc6eeb5b89323576e024da436a7f80d07ce9cdb6ba9f9808576cfd035a",
    "MomSeasonShort": "09e494a3da4041e53c9efcb3f9c7b269fef0967cd8010804b5a6f04c44e39d6d",
    "Mom6m": "7b1ee9dc26a477719423780e9e016dceb6880b5eabcb23ab625447178a105911",
    "Mom12m": "a5fef64b62bf64ae1babc66aa1d9483f6142dadac132f86ff0e53d081564d7ec",
}
EXPECTED_BOND_UNIT = "decimal"   # [2.1]
HY_MIN_SHARE = 0.5      # [4.3] an issuer is high-yield where at least half its rated bond value is non-investment grade
N_FIFTHS = 5            # [5.2]
NW_LAG = 3              # [6.2]
T_A, T_B, T_D = 3.0, 2.0, 2.0   # [7.1] thresholds on criteria (a), (b), (d)
T_WEAK = 2.0            # [7.2]
COST = 0.0025           # [6.4] 25 bp per unit of weight traded
IMPUTE = -0.30          # [6.6]
N_MIN_UNIVERSE = 100    # [5.3] eligible issuers needed for a month to count
N_MIN_LEG = 10          # [5.3] issuers with an outcome needed in each extreme fifth
N_MIN_FM = 50           # [6.3] issuers needed for a month's cross-sectional regression
T_MIN_MONTHS = 120      # [5.3] valid months needed, or the test is unscorable
VAL_TOL = 1e-3          # [3.3] absolute tolerance on a rebuilt Mom12m and on a re-derived seed
VAL_MIN_SHARE = 0.99    # [3.3] share of comparisons that must be within tolerance
VAL_MIN_COMPARABLE = 0.90  # [3.3] share of published Mom12m rows that can be rebuilt at all
FIRST_MI = 2002 * 12 + 7   # August 2002, the panel's first month


def say(*a):
    print(*a, flush=True)


# ----- statistics --------------------------------------------------------------------------------

def nw(x, lag=NW_LAG):
    """Mean of a series with a Newey-West standard error, Bartlett kernel, no small-sample correction.

    gamma_j = (1/T) * sum_{t=j+1..T} (x_t - m)(x_{t-j} - m);  V = gamma_0 + 2 * sum_{j=1..L} (1 - j/(L+1)) gamma_j
    se = sqrt(V / T);  t = m / se. The series is taken in month order; missing months are skipped and
    the remaining observations are treated as consecutive.
    """
    x = np.asarray(x, dtype="float64")
    x = x[np.isfinite(x)]
    T = len(x)
    if T < lag + 2:
        return {"n": T, "mean": None, "se": None, "t": None}
    m = x.mean()
    d = x - m
    v = float(d @ d) / T
    for j in range(1, lag + 1):
        v += 2.0 * (1.0 - j / (lag + 1.0)) * float(d[j:] @ d[:-j]) / T
    if not v > 0:
        return {"n": T, "mean": float(m), "se": None, "t": None}
    se = math.sqrt(v / T)
    return {"n": T, "mean": float(m), "se": se, "t": float(m / se)}


def assign_fifths(e, col):
    """Sort each month's eligible issuers by `col` ascending, ties broken by permno ascending, and cut
    into fifths: rank k = 1..N, fifth = floor(5 * (k - 1) / N) + 1. Fifth 5 holds the highest values."""
    e = e.sort_values(["mi", col, "permno"], kind="mergesort").copy()
    e["k"] = e.groupby("mi").cumcount() + 1
    e["n"] = e.groupby("mi")["permno"].transform("size")
    e["q"] = (N_FIFTHS * (e["k"] - 1) // e["n"]) + 1
    return e


def month_table(e, ycol, wcol=None):
    """Per formation month: universe size, and per fifth the count with an outcome and the mean outcome
    (equal-weighted, or weighted by `wcol` among members with an outcome)."""
    d = e[np.isfinite(e[ycol])]
    w = d[wcol].astype("float64") if wcol else pd.Series(1.0, index=d.index)
    g = pd.DataFrame({"mi": d["mi"], "q": d["q"], "w": w, "wy": w * d[ycol]}).groupby(["mi", "q"]).agg(w=("w", "sum"), wy=("wy", "sum"), c=("w", "size"))
    mean = (g["wy"] / g["w"]).unstack("q")
    cnt = g["c"].unstack("q").fillna(0).astype(int)
    out = pd.DataFrame({"n_univ": e.groupby("mi").size()})
    for q in range(1, N_FIFTHS + 1):
        out[f"r{q}"] = mean[q] if q in mean else np.nan
        out[f"c{q}"] = cnt[q] if q in cnt else 0
    gu = pd.DataFrame({"mi": d["mi"], "y": d[ycol]}).groupby("mi")["y"]
    out["ru"] = gu.mean()
    out["cu"] = gu.size()
    mid = d[d["q"].isin([2, 3, 4])].groupby("mi")[ycol].mean()
    out["rmid"] = mid
    out[[f"c{q}" for q in range(1, N_FIFTHS + 1)]] = out[[f"c{q}" for q in range(1, N_FIFTHS + 1)]].fillna(0).astype(int)
    out["valid"] = (out["n_univ"] >= N_MIN_UNIVERSE) & (out["c1"] >= N_MIN_LEG) & (out[f"c{N_FIFTHS}"] >= N_MIN_LEG)
    out["ls"] = out[f"r{N_FIFTHS}"] - out["r1"]
    return out.sort_index()


def long_short(e, ycol, wcol=None):
    mt = month_table(e, ycol, wcol)
    v = mt[mt["valid"]]
    s = nw(v["ls"].to_numpy())
    s["months_valid"] = int(len(v))
    s["months_seen"] = int(len(mt))
    s["mean_universe"] = float(v["n_univ"].mean()) if len(v) else None
    s["mean_leg_top"] = float(v[f"c{N_FIFTHS}"].mean()) if len(v) else None
    s["mean_leg_bottom"] = float(v["c1"].mean()) if len(v) else None
    s["share_positive"] = float((v["ls"] > 0).mean()) if len(v) else None
    return s, mt


def fama_macbeth(e, ycol, controls=True):
    """Monthly cross-sectional OLS of the outcome on an intercept, the rank of the signal and (with
    controls) the ranks of the stock's own month-t return and of Mom6m at t. Each rank is taken within
    the month's regression sample, ties by permno: (k - 1) / (n - 1) - 0.5, so a slope is the return
    difference across the full range of the regressor. Returns the series of slopes on the signal."""
    need = [ycol, "sig"] + (["r_t", "m6_t"] if controls else [])
    d = e[np.isfinite(e[need]).all(axis=1)]
    slopes = {}
    for mi, g in d.groupby("mi", sort=True):
        n = len(g)
        if n < N_MIN_FM:
            continue
        cols = [np.ones(n)]
        for c in (["sig"] + (["r_t", "m6_t"] if controls else [])):
            order = np.lexsort((g["permno"].to_numpy(), g[c].to_numpy()))
            rk = np.empty(n)
            rk[order] = np.arange(n)
            cols.append(rk / (n - 1) - 0.5)
        X = np.column_stack(cols)
        beta, *_ = np.linalg.lstsq(X, g[ycol].to_numpy(dtype="float64"), rcond=None)
        slopes[int(mi)] = float(beta[1])
    s = nw(np.array([slopes[k] for k in sorted(slopes)]))
    s["months"] = len(slopes)
    return s, slopes


def long_only(e, mt, ycol):
    """Top fifth minus the eligible universe, net of costs charged to the top fifth only.

    Weights at formation month t: 1 / n5 on each member of the top fifth (all members, whether or not
    an outcome is later recovered). cost_t = COST * sum_i |w_t,i - w_{t-1},i|, where w_{t-1} is the
    previous CALENDAR month's weight vector and is zero where that month has no top fifth.
    net_t = r5_t - cost_t - ru_t, over the months valid for the long-short series.
    """
    top = e[e["q"] == N_FIFTHS][["mi", "permno", "n"]].copy()
    n5 = top.groupby("mi")["permno"].transform("size")
    top["w"] = 1.0 / n5
    prev = top[["mi", "permno", "w"]].rename(columns={"w": "w_prev"})
    prev["mi"] = prev["mi"] + 1
    m = top.merge(prev, on=["mi", "permno"], how="outer")
    m["w"] = m["w"].fillna(0.0)
    m["w_prev"] = m["w_prev"].fillna(0.0)
    traded = (m["w"] - m["w_prev"]).abs().groupby(m["mi"]).sum()
    v = mt[mt["valid"]].copy()
    v["traded"] = traded.reindex(v.index)
    v["cost"] = COST * v["traded"]
    v["net"] = v[f"r{N_FIFTHS}"] - v["cost"] - v["ru"]
    v["gross"] = v[f"r{N_FIFTHS}"] - v["ru"]
    s = nw(v["net"].to_numpy())
    s["gross_mean"] = float(v["gross"].mean()) if len(v) else None
    s["gross_t"] = nw(v["gross"].to_numpy())["t"]
    s["mean_cost"] = float(v["cost"].mean()) if len(v) else None
    s["mean_one_way_turnover"] = float(v["traded"].mean() / 2.0) if len(v) else None
    s["mean_names_top_fifth"] = float(top.groupby("mi").size().reindex(v.index).mean()) if len(v) else None
    return s


# ----- inputs ------------------------------------------------------------------------------------

def refuse(res, reason, detail=""):
    res["verdict"] = "UNSCORABLE"
    res["refusal"] = {"reason": reason, "detail": detail}
    say(f"REFUSED TO SCORE: {reason}. {detail}")


def load_inputs(res, tmp):
    """Download both inputs, check them against the pins, and return (panel frame, signal frames).
    Any mismatch raises Refusal; nothing downstream runs."""
    if "PENDING" in set(EXPECTED.values()) | {EXPECTED_BOND_UNIT}:
        raise cdlib.Refusal("pins_not_set", "the specification's input pins were never filled in")
    rel = cdlib.release_assets(os.environ.get("GH_TOKEN"))
    asset = [a for a in rel["assets"] if a["name"] == cdlib.OSBAP_ASSET]
    if len(asset) != 1:
        raise cdlib.Refusal("panel_asset_not_found", cdlib.OSBAP_ASSET)
    dest = os.path.join(tmp, cdlib.OSBAP_ASSET)
    n, sha, _ = cdlib.download_to(asset[0]["url"], dest)
    res["inputs"]["panel_zip"] = {"bytes": n, "sha256": sha}
    if sha != EXPECTED["panel_zip_sha256"]:
        raise cdlib.Refusal("input_hash_mismatch", f"{cdlib.OSBAP_ASSET}: {sha}")
    members = {name: (path, size) for name, path, size in cdlib.extract_parquet_members(dest, os.path.join(tmp, "x"))}
    if EXPECTED["panel_member"] not in members:
        raise cdlib.Refusal("panel_member_missing", EXPECTED["panel_member"])
    path = members[EXPECTED["panel_member"]][0]
    msha = cdlib.sha256_file(path)
    res["inputs"]["panel_member"] = {"name": EXPECTED["panel_member"], "sha256": msha}
    if msha != EXPECTED["panel_member_sha256"]:
        raise cdlib.Refusal("input_hash_mismatch", f"{EXPECTED['panel_member']}: {msha}")
    panel = cdlib.read_panel(path, cdlib.PANEL_REQUIRED)
    client = cdlib.new_osap_client()
    sig = {}
    for name in cdlib.SIGNALS:
        body, file_id = cdlib.fetch_signal_bytes(name, client)
        h = cdlib.sha256_bytes(body)
        res["inputs"][name] = {"bytes": len(body), "sha256": h, "drive_file_id": file_id}
        if h != EXPECTED[name]:
            raise cdlib.Refusal("input_hash_mismatch", f"{name}: {h}")
        sig[name], _ = cdlib.parse_signal(name, body)
        del body
    return panel, sig


def gates(res, panel, sig):
    """Units and the reconstruction's validation. Returns (issuer-month frame, stock structure)."""
    g = res["gates"]
    ub, _ = cdlib.unit_of(pd.to_numeric(panel["ret_vw"], errors="coerce").dropna().to_numpy(), "bond")
    ut, _ = cdlib.unit_of(pd.to_numeric(panel["tret"], errors="coerce").dropna().to_numpy(), "bond")
    g["bond_units"] = {"ret_vw": ub, "tret": ut}
    if not (ub == ut == EXPECTED_BOND_UNIT):
        raise cdlib.Refusal("bond_unit_unexpected", f"ret_vw {ub}, tret {ut}, expected {EXPECTED_BOND_UNIT}")
    us, _ = cdlib.unit_of(sig["MomSeasonShort"]["MomSeasonShort"].to_numpy(), "stock")
    g["stock_unit"] = us
    if us != "decimal":
        raise cdlib.Refusal("stock_unit_not_decimal", us)
    im = cdlib.issuer_months(panel)
    stk = cdlib.reconstruct(sig)
    hyp = np.unique(im.loc[im["hy_share"] >= HY_MIN_SHARE, "permno"].to_numpy(dtype="int64"))
    v1, v2 = cdlib.validate_mom12m(stk), cdlib.validate_roll_on_seeds(stk)
    m1 = np.isin(v1["key"] // cdlib.KEY_BASE, hyp) & ((v1["key"] % cdlib.KEY_BASE) >= FIRST_MI)
    m2 = np.isin(v2["key"] // cdlib.KEY_BASE, hyp) & ((v2["key"] % cdlib.KEY_BASE) >= FIRST_MI)
    val = {"mom12m_all": cdlib.error_summary(v1["err"][m1], VAL_TOL),
           "mom12m_rolled": cdlib.error_summary(v1["err"][m1 & v1["rolled"]], VAL_TOL),
           "roll_formula_on_seeds": cdlib.error_summary(v2["err"][m2], VAL_TOL),
           "mom12m_comparable_share": float(v1["complete"][m1].mean()) if m1.any() else 0.0}
    g["validation"] = val
    for k in ("mom12m_all", "mom12m_rolled", "roll_formula_on_seeds"):
        if val[k].get("n", 0) < 1000 or val[k]["share_within_tol"] < VAL_MIN_SHARE:
            raise cdlib.Refusal("reconstruction_not_validated", f"{k}: {val[k]}")
    if val["mom12m_comparable_share"] < VAL_MIN_COMPARABLE:
        raise cdlib.Refusal("reconstruction_not_validated", f"comparable share {val['mom12m_comparable_share']:.4f}")
    g["reconstruction"] = {"passes": stk["passes"], "panel_end": int(cdlib.yyyymm_from_mi(stk["panel_end"]))}
    return im, stk


# ----- the test ----------------------------------------------------------------------------------

def eligible(lk, universe, sig_col):
    if universe == "hy":
        m = lk["hy_share"] >= HY_MIN_SHARE
    elif universe == "ig":
        m = lk["hy_share"] < HY_MIN_SHARE
    else:
        m = pd.Series(True, index=lk.index)
    e = lk[m & lk["listed_t"] & np.isfinite(lk[sig_col])].copy()
    e["sig"] = e[sig_col]
    return assign_fifths(e, "sig")


def analyse(lk, res):
    lost = lk["reason"] == "t1_is_final_month_lost"
    lk = lk.copy()
    lk["y"] = lk["r_t1"]
    lk["y_e1"] = np.where(lost, IMPUTE, lk["r_t1"])
    lk["nCR"] = lk["CR"]
    lk["nDCS"] = -lk["DCS"]
    # three-month formation: the sum of CR over t-2, t-1, t, where the issuer has a row in all three
    k = lk[["permno", "mi", "CR"]]
    k1 = k.rename(columns={"CR": "CR1"}).assign(mi=k["mi"] + 1)
    k2 = k.rename(columns={"CR": "CR2"}).assign(mi=k["mi"] + 2)
    lk = lk.merge(k1, on=["permno", "mi"], how="left").merge(k2, on=["permno", "mi"], how="left")
    lk["CR3"] = lk["CR"] + lk["CR1"] + lk["CR2"]

    e = eligible(lk, "hy", "nCR")
    e["y_e2"] = np.where((e["reason"] == "t1_is_final_month_lost") & (e["q"] == N_FIFTHS), IMPUTE, e["y"])
    prim, mt = long_short(e, "y")
    res["primary"] = prim
    v = mt[mt["valid"]]
    T = len(v)
    if T < T_MIN_MONTHS:
        raise cdlib.Refusal("sample_below_floor", f"{T} valid months, {T_MIN_MONTHS} required")
    h = int(math.ceil(T / 2))
    halves = [nw(v["ls"].to_numpy()[:h]), nw(v["ls"].to_numpy()[h:])]
    fm, _ = fama_macbeth(e, "y", controls=True)
    lo = long_only(e, mt, "y")
    e1, _ = long_short(e, "y_e1")
    e2, _ = long_short(e, "y_e2")
    crit = {
        "a": {"met": bool(prim["mean"] > 0 and prim["t"] >= T_A), "mean": prim["mean"], "t": prim["t"], "threshold_t": T_A},
        "b": {"met": bool(fm["mean"] is not None and fm["mean"] > 0 and fm["t"] >= T_B), "slope": fm["mean"], "t": fm["t"], "months": fm["months"], "threshold_t": T_B},
        "c": {"met": bool(halves[0]["mean"] > 0 and halves[1]["mean"] > 0), "first_half": halves[0], "second_half": halves[1]},
        "d": {"met": bool(lo["mean"] > 0 and lo["t"] >= T_D), "threshold_t": T_D, **lo},
        "e1": {"met": bool(e1["mean"] > 0), "mean": e1["mean"], "t": e1["t"], "months_valid": e1["months_valid"]},
        "e2": {"met": bool(e2["mean"] > 0), "mean": e2["mean"], "t": e2["t"], "months_valid": e2["months_valid"]},
    }
    res["criteria"] = crit
    all_met = all(c["met"] for c in crit.values())
    if all_met:
        verdict = "PASS"
    elif prim["mean"] > 0 and prim["t"] >= T_WEAK:
        verdict = "WEAK"
    else:
        verdict = "FAIL"
    res["verdict"] = verdict

    # ----- everything below is SECONDARY: reported, labelled, and carries no weight in the verdict -----
    sec = {}
    sec["fifth_means"] = {f"q{q}": float(v[f"r{q}"].mean()) for q in range(1, N_FIFTHS + 1)}
    sec["universe_mean"] = float(v["ru"].mean())
    sec["tails"] = {"top_minus_middle": nw((v[f"r{N_FIFTHS}"] - v["rmid"]).to_numpy()), "middle_minus_bottom": nw((v["rmid"] - v["r1"]).to_numpy())}
    sec["fama_macbeth_no_controls"] = fama_macbeth(e, "y", controls=False)[0]
    sec["bond_value_weighted"] = long_short(e, "y", wcol="bond_value")[0]
    sec["investment_grade"] = long_short(eligible(lk, "ig", "nCR"), "y")[0]
    sec["all_issuers"] = long_short(eligible(lk, "all", "nCR"), "y")[0]
    sec["spread_change_signal"] = long_short(eligible(lk, "hy", "nDCS"), "y")[0]
    sec["three_month_formation"] = long_short(eligible(lk, "hy", "CR3"), "y")[0]
    yr = pd.Series((v.index.to_numpy() + 1) // 12, index=v.index)
    # S11: the widest adversarial bound. Every top-fifth member with a missing outcome, whatever the
    # reason, is given IMPUTE; the series is taken over the primary's valid months.
    e["y_s11"] = np.where((e["q"] == N_FIFTHS) & ~np.isfinite(e["y"]), IMPUTE, e["y"])
    mt11 = month_table(e, "y_s11")
    sec["adversarial_all_missing_top"] = nw(mt11.loc[v.index, "ls"].to_numpy())
    # S13: the same at -100%. Minus 30% is a convention, not a floor.
    e["y_s13"] = np.where((e["q"] == N_FIFTHS) & ~np.isfinite(e["y"]), -1.0, e["y"])
    sec["adversarial_all_missing_top_at_minus_100"] = nw(month_table(e, "y_s13").loc[v.index, "ls"].to_numpy())
    # S12: the long-only form on the e2 outcome vector, over e2's own valid months.
    sec["long_only_under_e2"] = long_only(e, month_table(e, "y_e2"), "y_e2")
    sec["by_outcome_year"] = {str(int(y)): {"months": int(len(g)), "mean_ls": float(g.mean())} for y, g in v["ls"].groupby(yr)}
    att = {}
    for q in range(1, N_FIFTHS + 1):
        sub = e[e["q"] == q]
        c = sub["reason"].value_counts()
        att[f"q{q}"] = {"members": int(len(sub)), "share_with_outcome": float(np.isfinite(sub["y"]).mean()),
                        "final_month_lost": int(c.get("t1_is_final_month_lost", 0)), "t_is_final_month": int(c.get("t_is_final_month", 0)),
                        "other_missing": int(len(sub) - np.isfinite(sub["y"]).sum() - c.get("t1_is_final_month_lost", 0) - c.get("t_is_final_month", 0))}
    sec["attrition_by_fifth"] = att
    res["secondary"] = sec
    res["monthly"] = {"columns": ["outcome_yyyymm", "long_short", "n_universe", "n_top_with_outcome", "n_bottom_with_outcome"],
                      "rows": [[int(cdlib.yyyymm_from_mi(mi + 1)), round(float(r.ls), 6), int(r.n_univ), int(getattr(r, f"c{N_FIFTHS}")), int(r.c1)]
                               for mi, r in zip(v.index, v.itertuples(index=False))]}
    res["sample"] = {"first_outcome_month": int(cdlib.yyyymm_from_mi(v.index.min() + 1)), "last_outcome_month": int(cdlib.yyyymm_from_mi(v.index.max() + 1)),
                     "months_valid": T, "months_seen": int(len(mt)), "eligible_issuer_months": int(len(e)),
                     "with_outcome": int(np.isfinite(e["y"]).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    res = {"what": "credit-drift frozen test (H1); non-evidentiary; outside the FNTN funnel", "verdict": None,
           "frozen": {f: cdlib.sha256_file(os.path.join(here, f)) for f in ("PREREG.md", "run.py", "cdlib.py", "verify.py") if os.path.exists(os.path.join(here, f))},
           "commit": os.environ.get("GITHUB_SHA"), "inputs": {}, "gates": {}, "parameters": {
               "HY_MIN_SHARE": HY_MIN_SHARE, "NW_LAG": NW_LAG, "T_A": T_A, "T_B": T_B, "T_D": T_D, "T_WEAK": T_WEAK, "COST": COST, "IMPUTE": IMPUTE,
               "N_MIN_UNIVERSE": N_MIN_UNIVERSE, "N_MIN_LEG": N_MIN_LEG, "N_MIN_FM": N_MIN_FM, "T_MIN_MONTHS": T_MIN_MONTHS,
               "VAL_TOL": VAL_TOL, "VAL_MIN_SHARE": VAL_MIN_SHARE, "VAL_MIN_COMPARABLE": VAL_MIN_COMPARABLE, "GUARD": cdlib.GUARD}}
    code = 0
    tmp = tempfile.mkdtemp(prefix="cd_", dir=os.environ.get("RUNNER_TEMP") or None)
    try:
        panel, sig = load_inputs(res, tmp)
        im, stk = gates(res, panel, sig)
        del panel, sig
        lk = cdlib.link(im, stk)
        analyse(lk, res)
    except cdlib.Refusal as r:
        refuse(res, r.reason, r.detail)
        code = 2
    with open(os.path.join(args.out, "results.json"), "w") as f:
        json.dump(res, f, indent=1, sort_keys=True, default=str)
    say("\nVERDICT:", res["verdict"])
    if res.get("criteria"):
        for k, c in res["criteria"].items():
            flat = dict(c)
            for hk in ("first_half", "second_half"):
                if hk in flat:
                    flat[hk + "_mean"] = flat.pop(hk)["mean"]
            say(f"  criterion {k}: {'met' if c['met'] else 'NOT met'} | " + ", ".join(f"{a}={b:.5g}" for a, b in flat.items() if isinstance(b, float)))
        say("  primary:", {k: (round(x, 6) if isinstance(x, float) else x) for k, x in res["primary"].items()})
        say("  sample:", res["sample"])
        say("  secondary (no weight in the verdict):")
        for k, x in res["secondary"].items():
            say(f"    {k}: {x}")
    return code


if __name__ == "__main__":
    sys.exit(main())
