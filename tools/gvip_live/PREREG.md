# Pre-registration: the live GVIP ETF, six-factor alpha and Nasdaq 100 comparison

Written 29 October 2026, before any GVIP return was retrieved. Study 1 of the follow-up plan to
`docs/VIP_PREMIUM_2026-10-29.md`, which found no six-factor alpha (1.35% a year, t 1.36) in a
reconstructed hedge-fund VIP basket subject to survivorship bias and costless rebalancing. The
Goldman Sachs Hedge Industry VIP ETF (GVIP) tracks Goldman's own VIP index with real fees, real
trading and no survivorship bias. A non-evidentiary side test outside the FNTN funnel; not
investment advice.

## 1. Hypothesis

**H-GVIP.** GVIP's monthly return earns a positive alpha against the Fama-French five factors plus
momentum. Registered sign positive; one-sided.

## 2. Inputs

- GVIP, SPY, QQQ and RSP daily adjusted closes, Yahoo via `yfinance` (`auto_adjust=True`), on SPY's
  trading days.
- Kenneth French daily five factors and momentum, as in `tools/vip_premium/PREREG.md`.

## 3. Method

Exactly `tools/vip_premium/PREREG.md` sections 3 and 4, with GVIP's daily return in place of the
basket's, implemented by importing that test's frozen `run.py` (`monthly`, `ols`, `nw_se`,
`analyse`), with two differences:

1. **First month:** the first full calendar month after GVIP's first trading day with a price.
2. **Minimum sample:** 96 months (GVIP has about ten years of history; the VIP test's 120 would
   make this test unreadable by construction). PASS when t >= 2.0 and annualised alpha >= 2.0% and
   at least 96 months are used; INSUFFICIENT below 96; FAIL otherwise.

Reported without weight: everything `tools/vip_premium` reports, of which the alpha on QQQ is the
comparison that matters for the operator, who already holds the Nasdaq 100.

## 4. Self-test, independent check, disclosures

1. `selftest.py` runs `tools/vip_premium/selftest.py` (the imported regression code) and checks
   that the 96-month threshold is applied.
2. `verify.py` is a second implementation by a separate agent from this document,
   `tools/vip_premium/PREREG.md` and the input formats alone; `compare.py` requires months, alpha,
   t and verdict to agree (alpha and t to 1e-6).
3. GVIP's returns are net of its expense ratio, so a PASS here would be an investable alpha; its
   index is Goldman's own construction, not Version B's.
4. The analyst is a language model with general knowledge of market history to mid-2026, including
   commentary on GVIP's performance; the sample is not unseen.
