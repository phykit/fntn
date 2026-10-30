"""Rows read directly from FNTN project documents that exist only in the claude.ai Project (no
repository copy). Each row quotes the source line. Written by the main session, which has the
Projects tool; subagents do not."""
import csv
import os

H = ["id", "date", "test", "hypothesis", "verdict", "primary_stat", "p", "p_basis", "source", "quote",
     "include", "exclude_reason", "notes"]
R = []


def row(**k):
    R.append([k.get(h, "") for h in H])


# 9 October: Fed liquidity / GDP
row(id="fedliq_h1", date="2026-10-09", test="Fed liquidity over GDP", hypothesis="H1 ratio above 12% goes with less funding stress",
    verdict="PASS", primary_stat="stress-day share, rotation test", p="0.013", p_basis="reported",
    source="project:claude/fedliq_gdp_test_2026-10-09.md",
    quote="Randomisation test, HIGH against the rest, 79 rotations: stress-day share p below 0.013 (no rotation as extreme)",
    include="yes", notes="p is an upper bound (1/79 resolution); a description of repo plumbing, not a return predictor")
row(id="fedliq_h2a", date="2026-10-09", test="Fed liquidity over GDP", hypothesis="H2a ratio predicts NDX 3m",
    verdict="FAIL", primary_stat="3m diff -0.91, two-sided p 0.66", p="0.67", p_basis="from_two_sided",
    source="project:claude/fedliq_gdp_test_2026-10-09.md",
    quote="| NDX | **3m (primary)** | 3.79 | 4.70 | **-0.91** | **0.66** | -0.59 |", include="yes", notes="wrong sign")
row(id="fedliq_h2b", date="2026-10-09", test="Fed liquidity over GDP", hypothesis="H2b ratio predicts 10y Treasury 3m",
    verdict="FAIL", primary_stat="3m diff -1.46, two-sided p 0.07", p="0.965", p_basis="from_two_sided",
    source="project:claude/fedliq_gdp_test_2026-10-09.md",
    quote="| 10-year Treasury | **3m (primary)** | -0.68 | 0.79 | **-1.46** | **0.07** | -1.85 |", include="yes", notes="wrong sign")
# 9 October: credit spread proxy
row(id="aaa_ha", date="2026-10-09", test="Aaa spread proxy, NDX", hypothesis="H-A widening precedes weaker NDX",
    verdict="FAIL", primary_stat="slope +0.63 (wrong sign)", p="0.65", p_basis="reported",
    source="project:claude/credit_spread_proxy_test_2026-10-09.md",
    quote="| Full-sample slope | +0.63 (expected negative); p 0.65; Newey-West t 0.39; R-squared 0.05% |",
    include="yes", notes="wrong sign; sidedness of the reported p not stated, kept as reported")
row(id="aaa_hb", date="2026-10-09", test="Aaa spread proxy, NDX", hypothesis="H-B wide spread precedes higher 12m NDX",
    verdict="FAIL", primary_stat="slope -3.2 (wrong sign)", p="0.65", p_basis="reported",
    source="project:claude/credit_spread_proxy_test_2026-10-09.md",
    quote="477 months. Slope -3.2 (expected positive), p 0.65, Newey-West t -0.42.", include="yes", notes="wrong sign")
# 11 October: HY spread, S&P 500
row(id="hy_spx", date="2026-10-11", test="HY spread leads S&P 500", hypothesis="H1 widening precedes weaker index (5 days)",
    verdict="FAIL", primary_stat="5-day slope -0.040", p="0.306", p_basis="reported",
    source="project:claude/hy_spread_spx_test_2026-10-11.md",
    quote="| **5 days (primary)** | **-0.040** | -0.014 | -0.33 | **0.306** | 0.34 | +0.005 | 0.48 |", include="yes")
# 12 October: copper, COPX
row(id="copper_hl", date="2026-10-12", test="LME copper premium, COPX", hypothesis="HL premium level predicts COPX",
    verdict="FAIL", primary_stat="5-day slope +0.025", p="0.49", p_basis="reported",
    source="project:claude/copper_premium_copx_test_2026-10-12.md",
    quote="| Rotation p, registered sign | 0.49 | 0.90 |", include="yes")
row(id="copper_hc", date="2026-10-12", test="LME copper premium, COPX", hypothesis="HC premium change predicts COPX",
    verdict="FAIL", primary_stat="5-day slope -0.042", p="0.90", p_basis="reported",
    source="project:claude/copper_premium_copx_test_2026-10-12.md",
    quote="| Rotation p, registered sign | 0.49 | 0.90 |", include="yes", notes="wrong sign")
# 12 October: NQ futures premium
for k, (h, eff, p) in {"A": ("premium level", "-0.006%", "0.62"), "B": ("widening premium", "-0.024%", "0.90"),
                       "C": ("premium over fair value", "-0.068%", "0.93"),
                       "CD": ("above vs below fair value", "-0.127%", "0.83"),
                       "E": ("change in premium over fair value", "-0.021%", "0.87")}.items():
    row(id=f"nq_{k}", date="2026-10-12", test="NQ futures premium, QQQ", hypothesis=h, verdict="FAIL",
        primary_stat=f"5-day effect {eff}", p=p, p_basis="reported",
        source="project:claude/ndx_futures_premium_test_2026-10-12.md",
        quote=f"row {k}: effect {eff}, p stated sign {p}", include="yes", notes="wrong sign; in-test Bonferroni 0.005")


from statistics import NormalDist


def pt(t):
    """One-sided p in the registered direction from a t already signed in that direction."""
    return f"{1 - NormalDist().cdf(t):.4f}"


S = "project:claude/"
# 24 October: NFCI on the NDX (current vintage) and its replications
row(id="nfci_h1", date="2026-10-24", test="NFCI change, NDX (current vintage)", hypothesis="H1 weekly tightening precedes weaker NDX",
    verdict="PASS", primary_stat="4-week slope -1.50% per SD, t -4.28", p="0.0005", p_basis="reported",
    source=S + "nfci_ndx_test_2026-10-24.md", quote="| **4 weeks (primary)** | **-1.50%** | -0.23 | **-4.28** | **0.0005** | 0.98 | **+3.2%** |",
    include="yes", notes="p is the rotation floor; shown the same day to be a revision artefact (first-release replication FAIL, wrong sign)")
row(id="nfci_h2", date="2026-10-24", test="NFCI level, NDX", hypothesis="H2 tight conditions precede weaker NDX", verdict="FAIL",
    primary_stat="-0.13% per SD, t -0.37", p="0.25", p_basis="reported", source=S + "nfci_ndx_test_2026-10-24.md",
    quote="| H2, level: tight conditions are followed by weaker NDX returns | **FAIL (right sign, not significant)**: 1 of 7 | -0.13% per SD, t -0.37, rotation p 0.25", include="yes")
row(id="nfci_rt", date="2026-10-24", test="NFCI change, first release, NDX", hypothesis="replication of H1 on vintages", verdict="FAIL",
    primary_stat="+0.25% per SD (wrong sign)", p="0.85", p_basis="reported", source=S + "nfci_rt_replication_2026-10-24.md",
    quote="| **4 weeks (primary)** | **+0.25%** | **+0.59** | **0.85** | 1.19 | **-1.8%** |", include="yes")
row(id="nfci_spx", date="2026-10-24", test="NFCI change, first release, S&P 500", hypothesis="replication on S&P 500", verdict="FAIL",
    primary_stat="+0.293% per SD (wrong sign)", p="0.918", p_basis="reported", source=S + "nfci_spx_replication_2026-10-24.md",
    quote="| 4 | +0.293 | +0.94 | 0.918 | -1.29% |", include="yes")
# 24 October: risk5
for k, h, stat, p, basis, q in [
        ("S1", "first-release NFCI level forecasts volatility beyond VIX", "t -0.17 (wrong sign)", pt(-0.17), "wrong_sign_from_t", "| S1 | **FAIL, wrong sign** | NFCI coefficient -0.026 on log future volatility (per index point), t -0.17 | 0.44 | 0 of 3 |"),
        ("S2", "realised-volatility targeting of the NDX", "alpha +0.19% a month, t 2.30", pt(2.30), "from_t", "| S2 | **FAIL, right sign, not significant** (near miss) | alpha +0.19% a month, t 2.30 | 0.23 | 3 of 3 |"),
        ("S3", "VXN targeting of the NDX", "alpha +0.03% a month, t 0.61", pt(0.61), "from_t", "| S3 | **FAIL, right sign, not significant** | alpha +0.03% a month, t 0.61 | 0.12 | 2 of 3 |"),
        ("S4", "variance risk premium predicts 3-month NDX", "rotation p 0.39", "0.39", "reported", "| S4 | **FAIL, right sign, not significant** | +0.15% over 3 months per SD, t 0.13, rotation p 0.39 | 3.21 per SD | 0 of 3 |"),
        ("S5", "NDX return leads HYG less IEF", "rotation p 0.25", "0.25", "reported", "| S5 | **FAIL, right sign, not significant** | +0.04% next week per SD of NDX weekly return, t 0.40, rotation p 0.25 | 0.27 per SD | 0 of 3 |")]:
    row(id=f"risk5_{k}", date="2026-10-24", test="Five risk-state strategies", hypothesis=h, verdict="FAIL", primary_stat=stat, p=p,
        p_basis=basis, source=S + "risk5_test_2026-10-24.md", quote=q, include="yes", notes="in-test bar one-sided 0.005")
# 24 October: vt5
for k, h, t in [("V1", "downside volatility", 2.49), ("V2", "conditional cut", 2.19), ("V3", "EWMA volatility", 1.81),
                ("V4", "weekly rebalancing", 2.36), ("V5", "ten-month trend overlay", 1.50)]:
    row(id=f"vt5_{k}", date="2026-10-24", test="Volatility-targeting enhancements, NDX", hypothesis=h, verdict="FAIL",
        primary_stat=f"NDX alpha t {t}", p=pt(t), p_basis="from_t", source=S + "vt5_test_2026-10-24.md",
        quote=f"| {k} | ... | {t} | ... | (vt5 verdict table)", include="yes",
        notes="same NDX sample as risk5 S2; strongly dependent; in-test bar t 2.576 plus holdout replication")
row(id="vt5_R0", date="2026-10-24", test="Volatility targeting replication, four holdout markets", hypothesis="R0 S2 replicates",
    verdict="DOES NOT REPLICATE", primary_stat="0 of 4 markets", p="NA", p_basis="NA", source=S + "vt5_test_2026-10-24.md",
    quote="**R0, S2 replication: DOES NOT REPLICATE (0 of 4 markets).**", include="yes", notes="count criterion, no p; enters as 1")
# 24 October: rev5
for k, h, stat, p, basis, q in [
        ("H1", "observable revision predicts NDX", "rotation p 0.98 (wrong sign)", "0.98", "reported", "| H1 | Revision at release t ... | **FAIL, wrong sign** | +0.30% per SD, t +1.55, rotation p 0.98 (registered negative) |"),
        ("H2", "first-release Risk subindex change", "t +0.64 (wrong sign)", pt(-0.64), "wrong_sign_from_t", "| H2 | First-release change in the Risk subindex | **FAIL, wrong sign** | +0.29% per SD, t +0.64 | 0 of 4 |"),
        ("H3", "revision in HAR volatility model", "t +0.33", pt(0.33), "from_t", "| H3 | Revision in a HAR volatility model with the VIX | **FAIL, right sign, not significant** | coefficient +0.13 ..., t +0.33 | 0 of 3 |"),
        ("H4", "false-alarm NFCI tightening rebound", "rotation p 0.015", "0.015", "reported", "| H4 | \"False alarm\" ... | **FAIL, right sign, not significant** (near miss) | +2.2 points over 4 weeks above the average, 24 events, rotation p 0.015 | **3 of 3** |"),
        ("H5", "first-release level predicts left tail", "rotation p 0.25", "0.25", "reported", "| H5 | ... | **FAIL, right sign, not significant** | -3.6 per index point, rotation p 0.25 | 1 of 3 (SPX sign) |")]:
    row(id=f"rev5_{k}", date="2026-10-24", test="Real-time NFCI strategies", hypothesis=h, verdict="FAIL", primary_stat=stat, p=p,
        p_basis=basis, source=S + "rev5_test_2026-10-24.md", quote=q, include="yes",
        notes="H4 p after a post-run tie-rounding correction (frozen code gave 0.039)" if k == "H4" else "")
# 24 October: fa3
for k, h, p, q in [("Q1", "unconfirmed VIX spikes rebound more (Baa)", "0.24", "Delta +0.67 points over 20 days, rotation p 0.24 (bar 0.0083)"),
                   ("Q2", "unconfirmed by Baa and TED", "0.37", "Delta +0.41, p 0.37"),
                   ("Q3", "continuous version", "0.034", "difference +5.66, t 1.79, p 0.034")]:
    row(id=f"fa3_{k}", date="2026-10-24", test="Unconfirmed fear spikes, 1992 to 2011", hypothesis=h, verdict="FAIL", primary_stat=q,
        p=p, p_basis="reported", source=S + "fa3_test_2026-10-24.md", quote=q, include="yes")
# 25 October
row(id="month_end_H1", date="2026-10-25", test="Pre-month-end reversal, S&P 500", hypothesis="H1 T-3 to T+3", verdict="FAIL",
    primary_stat="+27 bp, NW t 1.01", p=pt(1.01), p_basis="from_t", source=S + "month_end_reversal_test_2026-10-25.md",
    quote="| H1 | T-3 to T+3 | **FAIL, right sign, not significant** | +27 bp | 1.01 | 75 bp | (b), (c), (d); not (a) |", include="yes")
row(id="month_end_H2", date="2026-10-25", test="Pre-month-end reversal, S&P 500", hypothesis="H2 settlement-adjusted window", verdict="FAIL",
    primary_stat="+18 bp, NW t 0.71", p=pt(0.71), p_basis="from_t", source=S + "month_end_reversal_test_2026-10-25.md",
    quote="| H2 | T-s to T+3 | **FAIL, right sign, not significant** | +18 bp | 0.71 | 69 bp | (c); not (a), (b), (d) |", include="yes")
for k, h, p, q in [("H1", "dealer tightening precedes NDX corrections", "0.34", "Net tightening before peaks -1.9%, in calm quarters -6.9%, difference +5.0 points, rotation p 0.34"),
                   ("H2", "published survey predicts next-quarter drawdown", "0.52", "Slope -0.006 (wrong sign), correlation -0.02, p 0.52"),
                   ("H3", "easing precedes trough", "1.00", "Easing leads the trough in 2 of 17 episodes; on the publication date, 0 of 17; sign p 1.00")]:
    row(id=f"scoos_{k}", date="2026-10-25", test="SCOOS dealer terms, NDX", hypothesis=h, verdict="FAIL", primary_stat=q, p=p,
        p_basis="reported", source=S + "scoos_haircut_ndx_test_2026-10-25.md", quote=q, include="yes")
for k, h, p, q in [("P1", "four-week cut in leveraged-fund net position precedes higher NDX", "0.49", "-0.002% per SD, NW t -0.01, rotation p 0.49"),
                   ("P2", "extreme net short precedes higher NDX", "0.33", "-0.11% per SD, t -0.52, rotation p 0.33")]:
    row(id=f"cftc_{k}", date="2026-10-25", test="CFTC leveraged funds, NQ", hypothesis=h, verdict="FAIL", primary_stat=q, p=p,
        p_basis="reported", source=S + "cftc_levfunds_ndx_test_2026-10-25.md", quote=q, include="yes",
        notes="consolidated-contract versions treated as replications within the test, not separate rows")
for k, h, p, q in [("Q1", "large-cap reversal pays more when VIX high", "0.62", "Slope -0.007% per VIX point (wrong sign), rotation p 0.62"),
                   ("Q2", "large-cap reversal pays more in NDX drawdowns", "0.26", "+0.31% a month more in drawdown months (rotation p 0.26)")]:
    row(id=f"stress_{k}", date="2026-10-25", test="Large-cap reversal in stress", hypothesis=h, verdict="FAIL", primary_stat=q, p=p,
        p_basis="reported", source=S + "stress_reversal_test_2026-10-25.md", quote=q, include="yes")
row(id="trend10_9", date="2026-10-25", test="Ten-month trend rule, nine holdout markets", hypothesis="timing beats scrambled timing (pooled Ulcer)",
    verdict="WEAK", primary_stat="mean ln(U_T/U_H) -0.33", p="0.004", p_basis="reported", source=S + "trend_drawdown_test_2026-10-25.md",
    quote="| (a) **timing, primary** | pooled Ulcer index below scrambled timing, rotation p <= 0.025 | **Met**: mean ln(U_T / U_H) -0.33, p 0.004 |", include="yes")
row(id="trend_blend", date="2026-10-25", test="Blended 1-3-12 month trend rule", hypothesis="pooled Ulcer below static mix",
    verdict="FAIL", primary_stat="mean ln(U_B/U_S) +0.13 (wrong sign)", p="0.032", p_basis="reported", source=S + "blend_trend_test_2026-10-25.md",
    quote="| **(a) primary** | pooled Ulcer index below the static mix, rotation p <= 0.025 | **Not met**: mean ln(U_B / U_S) **+0.13** (worse than the static mix), p 0.032 |",
    include="yes", notes="the statistic has the wrong sign; the reported p appears to be the timing-versus-random comparison. Kept as reported, which favours this row; it cannot become a discovery at the observed rank")
row(id="trend10_fresh", date="2026-10-25", test="Ten-month trend rule, ten fresh markets", hypothesis="timing replicates (pooled Ulcer)",
    verdict="WEAK", primary_stat="mean ln(U_T/U_H) -0.26", p="0.012", p_basis="reported", source=S + "fresh_trend_test_2026-10-25.md",
    quote="| (a) **timing replicates, primary** | pooled Ulcer below scrambled timing, rotation p <= 0.025 | **Met**: mean ln(U_T / U_H) -0.26, p 0.012 |", include="yes")


def write(path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(H)
        w.writerows(R)


if __name__ == "__main__":
    write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_manual.csv"))
    print(len(R), "rows")
