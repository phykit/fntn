# Pre-registration: two checks on the de-gross episode results

Written 29 October 2026, before either check was run. Non-evidentiary side checks outside the FNTN
funnel; not investment advice.

## Check 1: independent implementation of study 2, with leave-one-out

- An agent that has not read `tools/crowd_degross/run.py` writes `tools/checks/verify2.py` from
  `tools/crowd_degross/PREREG.md` and the input formats alone, and it is run on the same runner
  inputs as `run.py`.
- **Agreement:** the primary (GVIP minus QQQ, Class D, E0) n, mean, unconditional mean, p_lower and
  verdict, and every secondary series' E0 mean, must agree with `results_frozen21.json` to 1e-9 on
  means and exactly on n and verdict. Permutation p-values must agree exactly if the draw order is the
  same, else within 0.005. Disagreement is reported, and the first implementation is not edited to
  match.
- **Leave-one-out (descriptive, no verdict weight):** the primary statistic and its p_lower
  recomputed nine times, each with one episode removed (by the same permutation method, 10,000
  draws, `default_rng(20261029)`). Reported: the largest p and the episode whose removal produces it.

## Check 2: independent re-coding of the episode list

- A second agent re-codes the 103 candidate articles of `tools/degross_episodes/candidates_log.csv`
  from a blinded, shuffled list (`tools/checks/candidates_blind.csv`: outlet, URL, publication date
  only; no decision, class, stated period or reason), applying `tools/degross_episodes/PREREG.md`
  section 2 and the judgement calls written there in `docs/DEGROSS_EPISODES_2026-10-29.md`. It reads
  no market data, no proxy or results file, and not the original candidates log, build script or
  episode list.
- **Agreement measures:** per article, include versus exclude and class (D, N, excluded), with
  Cohen's kappa; for articles both include, the coded week-end equal or not. After merging under the
  rules, the re-coded episode list against the frozen one: episodes matched within 7 days and of the
  same class.
- **Consequence (sensitivity, no verdict weight):** if the re-coded Class D list differs from the
  frozen one, study 2's primary is recomputed on the re-coded list by the frozen `run.py`, and
  reported beside the frozen result. Kappa of 0.6 or more is read as substantial agreement; below 0.4
  as weak, in which case the article states that the episode coding is not robust to the coder.
