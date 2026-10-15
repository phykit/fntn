"""Synthetic data for the self-tests and the local cross-check of the kill tests of 15 October 2026.
Touches no real observation. make(kind, seed, outdir) writes every input file the four tests read.

kind = "null": no planted relation anywhere.
kind = "planted": A, the expiring gas contract's return to its last day loads negatively on M in the
  window; B, the spread change loads negatively on M; C, VIXY's next-5-day return loads negatively
  on B; D, spot bitcoin's next-5-day return loads positively on M.
"""
import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cal  # noqa: E402


def weekdays(start, end):
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def write(path, header, rows):
    with open(path, "w") as f:
        f.write(header + "\n")
        for r in rows:
            f.write(",".join("" if (v is None or (isinstance(v, float) and v != v)) else (v if isinstance(v, str) else f"{v:.6f}") for v in r) + "\n")


def energy(kind, rng, days, outdir, asset):
    """Null world: contract 1 is a random walk, the residual M is AR(1) and the spot is derived as
    S = F1 / ((1 + M/100) exp(r tau)), so the spot converges to the future (the parent's finding) and
    the future's own path is independent of M. Planted world: A, on each contract's last day the
    contract takes a step against the window's mean residual; B, the spread's innovations over the
    five days after t load negatively on M_t."""
    import bisect
    N = len(days)
    rate = np.clip(2.0 + np.cumsum(rng.normal(0, 0.02, N)), 0.05, 6.0)
    lF1 = np.log(3.0) + np.cumsum(rng.normal(0.0, 3.0, N)) / 100.0
    Mt = np.zeros(N)
    for t in range(1, N):
        Mt[t] = 2.0 + 0.97 * (Mt[t - 1] - 2.0) + rng.normal(0, 1.0)
    exps = sorted(set(cal.expiry_for_delivery(asset, y, m) for (y, m) in cal.months_between(days[0], days[-1] + dt.timedelta(days=40))))
    xiso = [x.isoformat() for x in exps]
    diso = [d.isoformat() for d in days]
    kx = {}
    for X in exps:
        k = bisect.bisect_right(diso, X.isoformat()) - 1
        if k >= 0:
            kx[X] = k
    if kind == "planted":
        for X, k in kx.items():
            if k >= 4:
                step = -0.6 * np.mean(Mt[k - 4: k] - 2.0)
                lF1[k:] += step / 100.0
    Spt = np.zeros(N)
    for t in range(1, N):
        inn = rng.normal(0, 0.5)
        if kind == "planted" and t >= 1:
            inn += -0.12 * (Mt[t - 1] - 2.0)
        Spt[t] = 1.0 + 0.95 * (Spt[t - 1] - 1.0) + inn
    F1 = np.exp(lF1)
    S = np.zeros(N)
    for t, d in enumerate(days):
        k = bisect.bisect_right(xiso, d.isoformat())
        X = exps[k]
        tau = (X - d).days / 365.0
        S[t] = F1[t] / ((1 + Mt[t] / 100.0) * np.exp(rate[t] / 100.0 * tau))
    F2 = F1 * np.exp(Spt / 100.0)
    hol_s = set(rng.choice(N, 60, replace=False))
    hol_f = set(rng.choice(N, 60, replace=False))
    write(os.path.join(outdir, f"{asset}_spot.csv"), "DATE,VALUE", [(d.isoformat(), None if t in hol_s else S[t]) for t, d in enumerate(days)])
    write(os.path.join(outdir, f"{asset}_c1.csv"), "DATE,CLOSE", [(d.isoformat(), F1[t]) for t, d in enumerate(days) if t not in hol_f])
    if asset == "ng":
        write(os.path.join(outdir, "ng_c2.csv"), "DATE,CLOSE", [(d.isoformat(), F2[t]) for t, d in enumerate(days) if t not in hol_f])
    return rate


def vix(kind, rng, days, outdir):
    N = len(days)
    lv = np.zeros(N)
    for t in range(1, N):
        lv[t] = np.log(18.0) + 0.97 * (lv[t - 1] - np.log(18.0)) + rng.normal(0, 0.06)
    V = np.exp(lv)
    Bt = np.zeros(N)
    for t in range(1, N):
        Bt[t] = 8.0 + 0.9 * (Bt[t - 1] - 8.0) + rng.normal(0, 2.0)
    V3 = V * (1 + Bt / 100.0)
    ret = rng.normal(-0.1, 3.5, N)
    if kind == "planted":
        for lag in range(1, 6):
            ret[lag:] += -0.08 * (Bt[:-lag] - 8.0)
    on = rng.normal(0, 1.0, N)
    lC = np.zeros(N)
    lO = np.zeros(N)
    prev = np.log(100.0)
    for t in range(N):
        lO[t] = prev + on[t] / 100.0
        lC[t] = lO[t] + ret[t] / 100.0
        prev = lC[t]
    C, O = np.exp(lC), np.exp(lO)
    hol = set(rng.choice(N, 40, replace=False))
    write(os.path.join(outdir, "vix.csv"), "DATE,CLOSE", [(d.isoformat(), V[t]) for t, d in enumerate(days)])
    write(os.path.join(outdir, "vix3m.csv"), "DATE,CLOSE", [(d.isoformat(), V3[t]) for t, d in enumerate(days) if t not in hol])
    write(os.path.join(outdir, "etp.csv"), "DATE,OPEN,CLOSE,ADJCLOSE", [(d.isoformat(), O[t], C[t], C[t] * 0.5) for t, d in enumerate(days)])


def btc(kind, rng, days, outdir, rate):
    N = len(days)
    ret = rng.normal(0.1, 4.0, N)
    Mt = np.zeros(N)
    for t in range(1, N):
        Mt[t] = 0.8 + 0.95 * (Mt[t - 1] - 0.8) + rng.normal(0, 0.4)
    if kind == "planted":
        for lag in range(1, 6):
            ret[lag:] += 1.2 * (Mt[:-lag] - 0.8)
    S = 20000.0 * np.exp(np.cumsum(ret) / 100.0)
    import bisect
    exps = []
    y, m = days[0].year, days[0].month
    while (y, m) <= (days[-1].year, days[-1].month + 1 if days[-1].month < 12 else 12):
        d = (dt.date(y, m, 1) + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
        while d.weekday() != 4:
            d -= dt.timedelta(days=1)
        exps.append(d)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    xiso = [x.isoformat() for x in exps]
    F = np.zeros(N)
    for t, d in enumerate(days):
        k = bisect.bisect_right(xiso, d.isoformat())
        X = exps[min(k, len(exps) - 1)]
        tau = max((X - d).days, 0) / 365.0
        F[t] = S[t] * np.exp(rate[t] / 100.0 * tau) * (1 + Mt[t] / 100.0)
    # spot trades every day, futures weekdays only
    alld = []
    d = days[0]
    while d <= days[-1]:
        alld.append(d)
        d += dt.timedelta(days=1)
    Sall = {}
    k = 0
    for d in alld:
        if k < N - 1 and d > days[k]:
            k += 1
        Sall[d] = S[k] * np.exp(rng.normal(0, 0.5) / 100.0) if d.weekday() >= 5 else S[k]
    write(os.path.join(outdir, "btc_spot.csv"), "DATE,CLOSE", [(d.isoformat(), Sall[d]) for d in alld])
    write(os.path.join(outdir, "btc_fut.csv"), "DATE,CLOSE", [(d.isoformat(), F[t]) for t, d in enumerate(days)])


def make(kind, seed, outdir):
    rng = np.random.default_rng(seed)
    os.makedirs(outdir, exist_ok=True)
    days = weekdays(dt.date(1997, 1, 7), dt.date(2024, 4, 5))
    rate = None
    for asset in ("ng", "ho", "rb"):
        rate = energy(kind, rng, days, outdir, asset)
    write(os.path.join(outdir, "tbill.csv"), "DATE,RATE", [(d.isoformat(), None if t % 40 == 3 else rate[t]) for t, d in enumerate(days)])
    vdays = weekdays(dt.date(2011, 1, 4), dt.date(2026, 10, 14))
    vix(kind, rng, vdays, outdir)
    bdays = weekdays(dt.date(2017, 12, 18), dt.date(2026, 10, 15))
    brate = np.clip(2.0 + np.cumsum(rng.normal(0, 0.02, len(bdays))), 0.05, 6.0)
    with open(os.path.join(outdir, "tbill.csv"), "a") as f:
        for t, d in enumerate(bdays):
            if d > days[-1]:
                f.write(f"{d.isoformat()},{brate[t]:.6f}\n")
    btc(kind, rng, bdays, outdir, brate)


if __name__ == "__main__":
    make(sys.argv[1], int(sys.argv[2]), sys.argv[3])
