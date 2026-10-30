# Covered calls on a two-stock pair: does low correlation raise expected profit? Monte Carlo theory check

Opened 30 October 2026 on branch `covered-call-pair-mc-2026-10-30`. A non-evidentiary side test
outside the FNTN funnel; it produces no number about the world and authorises nothing.

- Pre-registration: `tools/covered_call_pair_mc/PREREG.md`, committed before any figure.
- Implementation: `tools/covered_call_pair_mc/run.py`; independent second implementation
  `verify.py` written by a separate agent from the pre-registration alone; `compare.py`;
  `selftest.py`; freeze record `FROZEN.sha256`.
- Run channel: `.github/workflows/covered-call-pair-mc.yml`, dispatched by a change to
  `tools/covered_call_pair_mc/DISPATCH`; results committed by the workflow under
  `tools/covered_call_pair_mc/results/<run>/`.
- Result write-up: to follow in this file once the run of record has completed.

§0.6 reading: this adds no gate, family, grammar row, cost tier, sizing input, feed or field the
funnel reads. It is procedure, outside the funnel, on its own branch; `main` is untouched.
