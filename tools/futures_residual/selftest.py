"""Self-test of run.py on synthetic data. Touches no real observation.

Worlds (weekdays 2000-01-03 to 2026-10-14, about 7,000 days, with holidays dropped from spot and
futures separately so the joint calendar is a real intersection):
  null       M independent of subsequent spot changes                      -> no PASS, (a) rare
  pos        spot's next 5 daily changes load positively on M              -> HL (a) met, sign +
  neg        as pos, negative loading                                      -> HL (a) met, sign -
  change     spot's next 5 daily changes load on dM                        -> HC (a) met
  momentum   spot changes load on their own past; M co-moves with spot     -> HL (d) and (e) not met
  roll       futures splice jumps at every expiry and nowhere else         -> roll steps counted,
                                                                              no |dM| > 5 within a contract
Also checks: the fair-value identity (M = 0 in a world with F = S exp(r tau)); the expiry rule on
known dates; NW with L = 0 against White; the rotation count; the OOS training cut-off.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as R  # noqa: E402


def weekdays(start, end):
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def expiries_ng(days):
    return [R.expiry_for_delivery("ng", y, m) for (y, m) in R.months_between(days[0], days[-1] + dt.timedelta(days=40))]


def world(kind, seed):
    rng = np.random.default_rng(seed)
    days = weekdays(dt.date(2000, 1, 3), dt.date(2026, 10, 14))
    N = len(days)
    rate = np.clip(2.0 + np.cumsum(rng.normal(0, 0.02, N)), 0.02, 6.0)
    ret = rng.normal(0.0, 3.0, N)                     # spot daily log change, %
    Mt = np.zeros(N)                                  # true residual path, pp
    for t in range(1, N):
        Mt[t] = 2.0 + 0.97 * (Mt[t - 1] - 2.0) + rng.normal(0, 1.0)
    if kind == "momentum":
        for t in range(1, N):
            ret[t] += 0.15 * ret[t - 1]
        for t in range(1, N):
            Mt[t] += 0.3 * ret[t]                     # M co-moves with the spot change
    if kind in ("pos", "neg"):
        c = 0.12 if kind == "pos" else -0.12
        for lag in range(1, 6):
            ret[lag:] += c * (Mt[:-lag] - 2.0)
    if kind == "change":
        dMt = np.concatenate([[0.0], np.diff(Mt)])
        for lag in range(1, 6):
            ret[lag:] += 0.4 * dMt[:-lag]
    S = 3.0 * np.exp(np.cumsum(ret) / 100.0)
    if kind == "zero":
        Mt[:] = 0.0
    # F from the test's own conventions: tau to the next NG expiry strictly after the day
    exps = sorted(set(expiries_ng(days)))
    F = np.zeros(N)
    roll = np.zeros(N)
    if kind == "roll":
        for X in exps:
            k = next((i for i, d in enumerate(days) if d > X), None)
            if k is not None:
                roll[k:] += rng.normal(0, 8.0)          # a permanent level shift at each roll
    for t, d in enumerate(days):
        X = next(x for x in exps if x > d)
        tau = (X - d).days / 365.0
        F[t] = S[t] * np.exp(rate[t] / 100.0 * tau) * (1 + (Mt[t] + roll[t]) / 100.0)
    return days, S, F, rate


def run_world(kind, seed):
    days, S, F, rate = world(kind, seed)
    rng = np.random.default_rng(seed + 100)
    N = len(days)
    hol_s = set(rng.choice(N, 60, replace=False))
    hol_f = set(rng.choice(N, 60, replace=False))
    with tempfile.TemporaryDirectory() as td:
        dd = os.path.join(td, "data")
        os.makedirs(dd)
        for asset in ("ng", "ho", "rb"):
            with open(os.path.join(dd, f"{asset}_spot.csv"), "w") as f:
                f.write("DATE,VALUE\n" + "".join(f"{d},{S[t]:.6f}\n" if t not in hol_s else f"{d},\n" for t, d in enumerate(days)))
            with open(os.path.join(dd, f"{asset}_fut.csv"), "w") as f:
                f.write("DATE,CLOSE\n" + "".join(f"{d},{F[t]:.6f}\n" for t, d in enumerate(days) if t not in hol_f))
        with open(os.path.join(dd, "tbill.csv"), "w") as f:
            f.write("DATE,RATE\n" + "".join(f"{d},{rate[t]:.2f}\n" if t % 40 != 3 else f"{d},\n" for t, d in enumerate(days)))
        out = os.path.join(td, "out")
        subprocess.run([sys.executable, os.path.join(HERE, "run.py"), "--data", dd, "--out", out, "--assets", "ng"],
                       check=True, capture_output=True)
        return json.load(open(os.path.join(out, "results.json")))["assets"]["ng"]


def main():
    fails = []
    # expiry rule on known dates (weekday arithmetic, no holiday calendar)
    checks = [("ng", 2026, 11, "2026-10-28"), ("ng", 2026, 3, "2026-02-25"), ("ng", 2025, 1, "2024-12-27"),
              ("ho", 2026, 11, "2026-10-30"), ("ho", 2026, 3, "2026-02-27")]
    for asset, y, m, want in checks:
        got = R.expiry_for_delivery(asset, y, m).isoformat()
        if got != want:
            fails.append(f"expiry {asset} {y}-{m:02d}: {got} != {want}")
    z = run_world("zero", 1)
    L = z["level_of_M"]
    print(f"zero-residual world: M mean {L['M_mean']:+.5f} p5 {L['M_p5']:+.5f} p95 {L['M_p95']:+.5f} (rate rounded to 0.01 and gaps filled, so small); "
          f"excluded {z['calendar']['excluded_days']} of {z['calendar']['joint_days']}; expiries {z['calendar']['expiries']}")
    if max(abs(L["M_p5"]), abs(L["M_p95"])) > 0.01:
        fails.append("fair value does not reproduce a zero-residual world")
    if z["roll_check"]["count_abs_dM_over_5pp"] > 0 or z["roll_check"]["roll_steps_over_5pp"] > 0:
        fails.append("roll check fires in a world with no roll")
    ne = z["calendar"]["expiries"]
    if not (ne * 6 - 30 <= z["calendar"]["excluded_days"] <= ne * 6 + 5):
        fails.append(f"exclusion count {z['calendar']['excluded_days']} not about {ne * 6}")

    nulls = [run_world("null", s) for s in range(1, 7)]
    na = sum(x["hypotheses"][h]["criteria"]["a_primary"] for x in nulls for h in ("HL", "HC"))
    npass = sum(x["hypotheses"][h]["verdict"].startswith("PASS") for x in nulls for h in ("HL", "HC"))
    print(f"null: (a) met in {na} of 12 hypothesis-worlds (expect 0 or 1); PASS in {npass}")
    if na > 2 or npass > 0:
        fails.append("null worlds pass too often")

    for kind, want in (("pos", 1), ("neg", -1)):
        w = [run_world(kind, s)["hypotheses"]["HL"] for s in range(1, 5)]
        print(f"{kind}: HL verdicts", [x["verdict"] for x in w], "t5", [round(x["by_h"]["5"]["nw_t"], 1) for x in w],
              "signs", [x["sign"] for x in w])
        if sum(x["criteria"]["a_primary"] and x["sign"] == want for x in w) < 3:
            fails.append(f"planted {kind} level not detected with the right sign")
    ch = [run_world("change", s)["hypotheses"]["HC"] for s in range(1, 5)]
    print("change: HC verdicts", [x["verdict"] for x in ch], "t5", [round(x["by_h"]["5"]["nw_t"], 1) for x in ch])
    if sum(x["criteria"]["a_primary"] for x in ch) < 3:
        fails.append("planted change not detected")
    mo = [run_world("momentum", s) for s in range(1, 4)]
    print("momentum: HL incremental t", [round(x["hypotheses"]["HL"]["incremental"]["nw_t"]["signal"], 1) for x in mo],
          "R2_OS", [round(x["hypotheses"]["HL"]["oos"]["r2_os"], 4) for x in mo],
          "n1 alone t(h=1)", [round(x["momentum_alone"]["n1"]["1"]["nw_t"], 1) for x in mo])
    if sum(x["hypotheses"]["HL"]["criteria"]["d_incremental"] for x in mo) > 1:
        fails.append("momentum world: incremental criterion met")
    rl = run_world("roll", 2)
    rc = rl["roll_check"]
    print(f"roll: steps >5pp {rc['roll_steps_over_5pp']} of {rc['n_roll_steps']} windows ({rl['calendar']['expiries']} expiries); "
          f"|dM|>5 within contracts {rc['count_abs_dM_over_5pp']}; max|dM| {rc['max_abs_dM']:.3f}")
    if rc["roll_steps_over_5pp"] < 0.3 * rc["n_roll_steps"]:
        fails.append("roll steps not counted")
    if rc["count_abs_dM_over_5pp"] > 0:
        fails.append("roll leaks into dM within a contract")

    # unit checks
    rng = np.random.default_rng(3)
    x = rng.normal(size=400)
    y = 0.2 * x + rng.normal(size=400) * (1 + abs(x))
    X = np.column_stack([np.ones(400), x])
    b, e, XtX_inv = R.ols(y, X)
    white = np.sqrt(np.diag(XtX_inv @ (X.T @ (X * (e ** 2)[:, None])) @ XtX_inv))
    if not np.allclose(R.nw_se(X, e, XtX_inv, 0), white):
        fails.append("NW L=0 is not White")
    xs, ys = rng.normal(size=100), rng.normal(size=100)
    rot = R.rot_slopes(xs, ys)
    if len(rot) != 59 or not np.isclose(rot[9], R.slope_only(np.roll(xs, -30), ys)):
        fails.append("rotation slopes wrong")
    m = 1300
    Mx = rng.normal(size=(m, 3))
    xx, yy = rng.normal(size=m), rng.normal(size=m)
    fb, fa, y0 = R.oos(yy, xx, Mx, m - 1, 5)
    y_out = yy.copy(); y_out[m - 5] += 5.0
    y_in = yy.copy(); y_in[m - 6] += 5.0
    if not np.allclose(R.oos(y_out, xx, Mx, m - 1, 5)[1], fa):
        fails.append("OOS uses a target not yet observed")
    if np.allclose(R.oos(y_in, xx, Mx, m - 1, 5)[1], fa):
        fails.append("OOS ignores the last observable target")
    print("SELFTEST", "FAILED: " + "; ".join(fails) if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
