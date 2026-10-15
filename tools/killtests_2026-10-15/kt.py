"""Shared estimators and the single-hypothesis verdict harness for the kill tests of 15 October 2026.

Each test's PREREG.md states these estimators in full; this file is one implementation of them, used
by every run_*.py. The independent verify_*.py scripts do not import it.
"""
import csv
import json

import numpy as np

MIN_SHIFT = 21
HORIZONS = [1, 5, 20]
PRIMARY = 5
FLOOR = 0.157


def num(v):
    v = v.strip()
    return float("nan") if v in ("", ".") else float(v.replace(",", ""))


def read(path, ncols):
    out = {}
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        if len(hdr) < ncols:
            raise SystemExit(f"{path}: expected {ncols} columns, header {hdr}")
        for row in rd:
            if not row or not row[0].strip():
                continue
            d = row[0].strip()
            if d in out:
                raise SystemExit(f"{path}: duplicate date {d}")
            out[d] = [num(row[k]) if k < len(row) else float("nan") for k in range(1, ncols)]
    return out


def ols(y, X):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    return beta, y - X @ beta, XtX_inv


def nw_se(X, resid, XtX_inv, L):
    m = len(resid)
    Xe = X * resid[:, None]
    S = Xe.T @ Xe
    for l in range(1, L + 1):
        if l >= m:
            break
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        S += w * (G + G.T)
    return np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))


def reg(y, cols, L):
    X = np.column_stack([np.ones(len(y))] + list(cols))
    beta, resid, XtX_inv = ols(y, X)
    se = nw_se(X, resid, XtX_inv, L)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / tss if tss > 0 else float("nan")
    return beta, se, r2


def slope_only(x, y):
    if len(x) < 3:
        return float("nan")
    xc = x - x.mean()
    den = float(xc @ xc)
    return float((xc @ (y - y.mean())) / den) if den > 0 else float("nan")


def rot_slopes(x, y):
    m = len(x)
    xc, yc = x - x.mean(), y - y.mean()
    den = xc @ xc
    return np.array([(np.roll(xc, -k) @ yc) / den for k in range(MIN_SHIFT, m - MIN_SHIFT + 1)])


def pvals(obs, rot):
    rot = rot[np.isfinite(rot)]
    K = len(rot)
    pp = float((1 + np.sum(rot >= obs)) / (1 + K))
    pm = float((1 + np.sum(rot <= obs)) / (1 + K))
    return {"shifts": int(K), "p_plus": pp, "p_minus": pm, "p2": min(1.0, 2.0 * min(pp, pm))}


def sign(b):
    if b is None or not np.isfinite(b):
        return 0
    return 1 if b > 0 else (-1 if b < 0 else 0)


def slope_stats(x, y, L):
    if len(x) < 2 * MIN_SHIFT + 2 or x.std() == 0:
        return {"n": int(len(x)), "slope": float("nan"), "slope_per_sd": float("nan"), "nw_t": float("nan"),
                "p_plus": float("nan"), "p_minus": float("nan"), "p2": float("nan"), "mde": float("nan"), "shifts": 0}
    beta, se, _ = reg(y, [x], L)
    b = float(beta[1])
    sd = float(x.std())
    out = {"n": int(len(x)), "slope": b, "slope_per_sd": b * sd, "sd_x": sd,
           "corr": float(np.corrcoef(x, y)[0, 1]), "nw_se": float(se[1]), "nw_t": b / float(se[1]),
           "nw_lag": int(L), "mde": 2.80 * float(se[1])}
    out.update(pvals(b, rot_slopes(x, y)))
    return out


def oos(y, x, M, start, h, with_x=True):
    m = len(y)
    Xb = np.column_stack([np.ones(m), M]) if M is not None and M.shape[1] > 0 else np.ones((m, 1))
    Xa = np.column_stack([Xb, x]) if with_x else np.ones((m, 1))
    cb_xx = np.cumsum(np.einsum("ti,tj->tij", Xb, Xb), axis=0)
    cb_xy = np.cumsum(Xb * y[:, None], axis=0)
    ca_xx = np.cumsum(np.einsum("ti,tj->tij", Xa, Xa), axis=0)
    ca_xy = np.cumsum(Xa * y[:, None], axis=0)
    fb, fa, yy = [], [], []
    for t in range(start, m):
        last = t - h
        fb.append(float(Xb[t] @ np.linalg.solve(cb_xx[last], cb_xy[last])))
        fa.append(float(Xa[t] @ np.linalg.solve(ca_xx[last], ca_xy[last])))
        yy.append(float(y[t]))
    return tuple(map(np.array, (fb, fa, yy)))


def oos_stats(fb, fa, yy):
    r2 = 1.0 - float(((yy - fa) ** 2).sum()) / float(((yy - fb) ** 2).sum())
    f = (yy - fb) ** 2 - ((yy - fa) ** 2 - (fb - fa) ** 2)
    beta, se, _ = reg(f, [], 10)
    return {"n_forecasts": int(len(yy)), "r2_os": r2, "cw_mean": float(beta[0]),
            "cw_nw_t": float(beta[0] / se[0]) if se[0] > 0 else float("nan")}


def hypothesis(x_all, R, base, sample, dates, oos_start, alpha2, extra_regime=None, lag_fn=None):
    """Sections 5 and 7 of each PREREG for one signal x_all against outcomes R[h], with baseline
    columns `base` (dict name -> array). All arrays on one calendar; `sample` is the boolean mask of
    signal days. Returns the hypothesis record with criteria and verdict."""
    def al(*arrs):
        m_ = sample.copy()
        for v in arrs:
            m_ &= np.isfinite(v)
        return m_

    L = lag_fn or (lambda h: h + 5)
    years = np.array([d[:4] for d in dates])
    H = {"by_h": {}}
    for h in HORIZONS:
        mk = al(x_all, R[h])
        H["by_h"][str(h)] = slope_stats(x_all[mk], R[h][mk], L(h))
    b = {h: H["by_h"][str(h)]["slope"] for h in HORIZONS}
    s = sign(b[PRIMARY])
    H["sign"] = s
    m5 = al(x_all, R[PRIMARY])
    x5, y5, yr5, d5 = x_all[m5], R[PRIMARY][m5], years[m5], dates[m5]
    half = len(x5) // 2
    H["halves"] = {"first": {"n": half, "from": str(d5[0]) if len(d5) else "n/a", "to": str(d5[half - 1]) if half else "n/a",
                             "slope": slope_only(x5[:half], y5[:half])},
                   "second": {"n": len(x5) - half, "from": str(d5[half]) if len(d5) > half else "n/a", "to": str(d5[-1]) if len(d5) else "n/a",
                              "slope": slope_only(x5[half:], y5[half:])}}
    names = list(base.keys())
    mi = al(x_all, *[base[k] for k in names], R[PRIMARY])
    if mi.sum() > len(names) + 3:
        beta, se, r2a = reg(R[PRIMARY][mi], [x_all[mi]] + [base[k][mi] for k in names], 10)
        _, _, r2b = reg(R[PRIMARY][mi], [base[k][mi] for k in names], 10) if names else (None, None, 0.0)
        H["incremental"] = {"n": int(mi.sum()), "coef": dict(zip(["const", "signal"] + names, map(float, beta))),
                            "nw_t": dict(zip(["const", "signal"] + names, map(float, beta / se))),
                            "r2_augmented": r2a, "r2_baseline": r2b}
    else:
        H["incremental"] = {"n": int(mi.sum()), "coef": {"signal": float("nan")}, "nw_t": {"signal": float("nan")},
                            "r2_augmented": float("nan"), "r2_baseline": float("nan")}
    Mb = np.column_stack([base[k][mi] for k in names]) if names else np.zeros((int(mi.sum()), 0))
    if mi.sum() > oos_start + 5:
        fb, fa, yy = oos(R[PRIMARY][mi], x_all[mi], Mb, oos_start, PRIMARY)
        H["oos"] = oos_stats(fb, fa, yy)
        H["oos"]["first_date"] = str(dates[mi][oos_start])
    else:
        H["oos"] = {"n_forecasts": 0, "r2_os": float("nan"), "cw_mean": float("nan"), "cw_nw_t": float("nan")}
    if s == 0 or len(x5) == 0:
        H["size"] = {"threshold": float("nan"), "n_top": 0, "Dq": 0.0}
    else:
        sx = s * x5
        Qthr = float(np.percentile(sx, 80))
        top = sx >= Qthr
        H["size"] = {"threshold": Qthr, "n_top": int(top.sum()), "Dq": float(y5[top].mean() - y5.mean())}
    # section 8 standard items
    reg_ = {"per_year": {}}
    for y in sorted(set(yr5)):
        s_ = yr5 == y
        if s_.sum() >= 20:
            reg_["per_year"][y] = {"n": int(s_.sum()), "slope": slope_only(x5[s_], y5[s_])}
    if extra_regime:
        for name, mask_all in extra_regime.items():
            mm = mask_all[m5]
            reg_[name] = {"in": {"n": int(mm.sum()), "slope": slope_only(x5[mm], y5[mm])},
                          "out": {"n": int((~mm).sum()), "slope": slope_only(x5[~mm], y5[~mm])}}
    H["regimes"] = reg_
    cut = int(np.floor(0.7 * len(x5)))
    H["holdout_last30"] = {"n": len(x5) - cut, "from": str(d5[cut]) if len(d5) > cut else "n/a", "slope": slope_only(x5[cut:], y5[cut:])}
    if len(x5) > 10:
        dev = np.abs(x5 - np.median(x5))
        c99 = float(np.percentile(dev, 99))
        loo = {y: slope_only(x5[yr5 != y], y5[yr5 != y]) for y in sorted(set(yr5))}
        fin = {k: v for k, v in loo.items() if np.isfinite(v)}
        H["influence"] = {"trim_cut": c99, "trim_dropped": int((dev >= c99).sum()),
                          "trim_slope": slope_only(x5[dev < c99], y5[dev < c99]), "leave_one_year_out": loo,
                          "min": {"year": min(fin, key=fin.get), "slope": min(fin.values())} if fin else {},
                          "max": {"year": max(fin, key=fin.get), "slope": max(fin.values())} if fin else {}}
        qb = np.percentile(x5, [20, 40, 60, 80])
        qq = np.searchsorted(qb, x5, side="left") + 1
        H["quintiles"] = {"breakpoints": list(map(float, qb)),
                          "R5": {str(k): {"n": int((qq == k).sum()), "mean": float(y5[qq == k].mean()) if (qq == k).any() else float("nan")}
                                 for k in range(1, 6)}}
    p2 = H["by_h"][str(PRIMARY)]["p2"]
    crit = {
        "a_primary": bool(s != 0 and np.isfinite(p2) and p2 <= alpha2),
        "b_horizons": bool(s != 0 and sign(b[1]) == s and sign(b[20]) == s),
        "c_halves": bool(s != 0 and sign(H["halves"]["first"]["slope"]) == s and sign(H["halves"]["second"]["slope"]) == s),
        "d_incremental": bool(s != 0 and sign(H["incremental"]["coef"]["signal"]) == s
                              and np.isfinite(H["incremental"]["nw_t"]["signal"]) and abs(H["incremental"]["nw_t"]["signal"]) >= 2.0),
        "e_oos": bool(np.isfinite(H["oos"]["r2_os"]) and H["oos"]["r2_os"] > 0),
        "f_size": bool(s != 0 and H["size"]["Dq"] >= FLOOR),
    }
    unscorable = H["by_h"][str(PRIMARY)]["shifts"] < 100
    if unscorable:
        crit = {k: False for k in crit}
        v = "UNSCORABLE"
    elif all(crit.values()):
        v = "PASS"
    elif crit["a_primary"]:
        v = "WEAK"
    else:
        v = "FAIL"
    H["criteria"], H["verdict"] = crit, f"{v} (sign {'+' if s > 0 else '-' if s < 0 else '0'})"
    return H


def fmt(v):
    return "nan" if v is None or not np.isfinite(v) else f"{v:+.4f}"


def print_h(label, H):
    print(f"  {label}: sign {H['sign']:+d}")
    for h in HORIZONS:
        t = H["by_h"][str(h)]
        p2 = t["p2"]
        print(f"    h={h} n={t['n']} slope={fmt(t['slope'])} per_sd={fmt(t.get('slope_per_sd'))} NW t={fmt(t['nw_t'])} "
              f"p2={'nan' if not np.isfinite(p2) else f'{p2:.4f}'} MDE={fmt(t['mde'])}")
    i, o, sz = H["incremental"], H["oos"], H["size"]
    print(f"    incremental g={fmt(i['coef']['signal'])} t={fmt(i['nw_t']['signal'])}; OOS n={o['n_forecasts']} R2_OS={fmt(o['r2_os'])} "
          f"CW t={fmt(o['cw_nw_t'])}; size Dq={fmt(sz['Dq'])} (n_top {sz['n_top']}); halves {fmt(H['halves']['first']['slope'])} / "
          f"{fmt(H['halves']['second']['slope'])}; holdout {fmt(H['holdout_last30']['slope'])}")
    if "quintiles" in H:
        print("    quintile means R5:", [round(H["quintiles"]["R5"][str(k)]["mean"], 3) for k in range(1, 6)])
    print("    criteria", json.dumps(H["criteria"]), "VERDICT:", H["verdict"])


def lagd(v, k):
    o = np.full(len(v), np.nan)
    o[k:] = v[k:] - v[:-k]
    return o
