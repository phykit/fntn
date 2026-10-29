# Pre-registration: does high-yield credit weakness lead the Nasdaq 100? (HYG against IEF, 2007 to 2026)

Written 29 October 2026, before any HYG, IEF or QQQ price was retrieved. Third test of the credit
spread idea (C. Kittson, 29 October 2026: a widening in high-yield spreads, for instance on doubts
about the returns on debt-financed AI investment, gives early warning of a Nasdaq 100 correction).
Non-evidentiary side test outside the FNTN funnel; not investment advice; authorises nothing.

## 0. Prior tests in this project (disclosed)

- 9 October 2026: Moody's Aaa and Baa spreads against the Nasdaq 100, 1986 to 2026: FAIL on direction
  and level; equity moves were followed by spread moves.
- 11 October 2026: ICE BofA US High Yield OAS (FRED, three years only) against the S&P 500, 1 to 20
  days: FAIL (right sign, not significant); the lead vanished once publication timing was respected.
- The gap this test closes: high-yield credit against the Nasdaq 100 over a long history. FRED no
  longer serves the ICE series beyond three years; this test uses a free market proxy instead.

## 1. Data

Yahoo Finance via yfinance, daily adjusted closes: **HYG** (iShares iBoxx USD High Yield Corporate
Bond ETF), **IEF** (iShares 7-10 Year Treasury Bond ETF), **QQQ** (Invesco QQQ, Nasdaq 100, total
return). Window: the first day all three have a close, to the latest close. Days are kept only where
all three have a close; t indexes those days.

## 2. Definitions

- Daily log returns h_t, i_t, q_t. **Credit excess return** c_t = h_t - i_t (high yield over
  Treasuries; negative when credit weakens relative to government bonds, the market counterpart of a
  widening spread).
- **Signal** S_t = c_(t-19) + ... + c_t, the 20-day credit excess return, known at the close of t.
- **Forward return**, executable: F_t = q_(t+2) + ... + q_(t+21), the QQQ log return over the 20
  trading days starting the day **after** the signal is known (one day for an order to be placed).
- Own-momentum control: M_t = q_(t-19) + ... + q_t.

## 3. Hypothesis and test

**H1 (registered): weaker credit is followed by a weaker Nasdaq 100.** In F_t = a + b S_t + e_t,
**b > 0**.

- **(a) primary:** b > 0 with one-sided circular-shift p <= 0.025. The shift p: S is rotated by every
  k with 250 <= k <= n - 250 against F (the aligned sample of n days); p = (1 + number of rotations
  with slope >= b) / (1 + number of rotations).
- **(b) incremental:** in F_t = a + b S_t + g M_t + e_t, b > 0 with Newey-West t (L = 20) >= 2.0.
  Because equities are known to lead credit, credit only matters if it adds to the index's own
  recent move.
- **(c) stability:** b > 0 in each half of the aligned sample.
- **(d) horizons:** with F over 5 and 10 days (same one-day delay), b > 0 at both.

**PASS:** all of (a) to (d). **WEAK:** (a) met, any other not; not actionable. **FAIL:** (a) not
met.

## 4. Reported without weight

1. Contemporaneous: correlation of c_t with q_t.
2. Reverse direction: slope of the next 20-day S (from t+2) on M_t, with Newey-West t.
3. Information convention (forward return from t+1, no delay): b and its shift p.
4. **Warning rule, the form an indicator would take.** Out of QQQ (into cash at 0%) from the
   close after S_t falls to or below the 10th percentile of all S up to t (expanding window, first
   504 days as burn-in, no signal before), back in when S_t rises above that day's 50th percentile
   (expanding). 10 bp per switch. Reported against buy-and-hold QQQ over the same days: annual
   return, volatility, maximum drawdown, share of time invested, number of exits; **false alarms**
   (exits after which QQQ was higher 20 days later), **missed declines** (QQQ drawdowns of 10% or
   more, peak to trough, during which the rule was invested at the trough), and the return given up
   in rallies while out.
5. The same rule driven by QQQ's own 20-day return M_t, as the benchmark any credit rule must beat.

## 5. Disclosures

1. HYG minus IEF is a proxy: HYG's duration (about 3 to 4 years) is shorter than IEF's (about 7 to
   8), so c_t also falls when Treasury yields fall. It is the free proxy that exists over this span.
2. Overlapping 20-day windows are handled by Newey-West and the circular-shift p.
3. The analyst is a language model with general knowledge of market history to mid-2026, including
   2008, 2020 and 2022; the sample is not unseen. The two prior tests' results are known.
4. A second implementation is written from this file alone and compared on every headline figure.
