# Single-stock option premium, systematic and idiosyncratic parts

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`, as the empirical follow-up to
`docs/COVERED_CALL_PAIR_MC_2026-10-30.md`. A non-evidentiary side test outside the FNTN funnel.
Pre-registration `tools/single_name_vrp/PREREG.md` (committed `a41ab08` before any input was
fetched); run channel `.github/workflows/single-name-vrp.yml`. Result write-up to follow here.

Run 1 (run id 41053140387) failed in the fetch step: FRED timed out on the runner before any
series was read, so no input and no figure exist from it. The fetcher gained a five-attempt retry
(the precedent fetcher's), `FROZEN.sha256` was re-stamped for `fetch.py` only, and the test was
re-dispatched. The analysis code and the pre-registration are unchanged.

Run 2 (run id 41053396172) failed the same way: FRED gave no response to five attempts. The input
source was then changed, before any input was read, to CBOE's own histories of the same indices;
the change is annotated in PREREG section 2 and `PREREG.md` and `fetch.py` were re-stamped.
