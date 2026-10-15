#!/usr/bin/env bash
# Kill tests of 15 October 2026: freeze check, self-test, fetch, the four frozen runs, the four
# independent implementations and the figure-by-figure comparison. Run from the repository root.
set -euo pipefail
T=tools/killtests_2026-10-15
mkdir -p out data
echo "== freeze check"
sha256sum $T/kt.py $T/cal.py $T/compare_all.py $T/synth.py $T/selftest_all.py $T/fetch_all.py \
  $T/a_expiry/PREREG.md $T/a_expiry/run_a.py $T/a_expiry/verify_a.py \
  $T/b_spread/PREREG.md $T/b_spread/run_b.py $T/b_spread/verify_b.py \
  $T/c_vix/PREREG.md $T/c_vix/run_c.py $T/c_vix/verify_c.py \
  $T/d_btc/PREREG.md $T/d_btc/run_d.py $T/d_btc/verify_d.py | tee out/frozen_as_run.sha256.txt
echo "committed FROZEN.sha256:" | tee -a out/frozen_as_run.sha256.txt
cat $T/FROZEN.sha256 | tee -a out/frozen_as_run.sha256.txt
for f in kt.py cal.py a_expiry/PREREG.md a_expiry/run_a.py a_expiry/verify_a.py b_spread/PREREG.md b_spread/run_b.py b_spread/verify_b.py \
         c_vix/PREREG.md c_vix/run_c.py c_vix/verify_c.py d_btc/PREREG.md d_btc/run_d.py d_btc/verify_d.py; do
  want="$(grep " $T/$f\$" $T/FROZEN.sha256 | awk '{print $1}')"
  have="$(sha256sum $T/$f | awk '{print $1}')"
  if [ "$want" != "$have" ]; then echo "::error::$f differs from the freeze record"; exit 1; fi
done
echo "freeze record verified" | tee -a out/frozen_as_run.sha256.txt
echo "== self-test"
python $T/selftest_all.py 2>&1 | tee out/selftest.log
echo "== fetch"
python $T/fetch_all.py --data data 2>&1 | tee out/fetch.log
echo "== run A"
python $T/a_expiry/run_a.py --data data --out out 2>&1 | tee out/run_a.log
echo "== run B"
python $T/b_spread/run_b.py --data data --out out 2>&1 | tee out/run_b.log
echo "== run C"
python $T/c_vix/run_c.py --data data --out out 2>&1 | tee out/run_c.log
echo "== run D"
python $T/d_btc/run_d.py --data data --out out 2>&1 | tee out/run_d.log
echo "== independent implementations"
python -I $T/a_expiry/verify_a.py --data data --out out 2>&1 | tee out/verify_a.log
python -I $T/b_spread/verify_b.py --data data --out out 2>&1 | tee out/verify_b.log
python -I $T/c_vix/verify_c.py --data data --out out 2>&1 | tee out/verify_c.log
python -I $T/d_btc/verify_d.py --data data --out out 2>&1 | tee out/verify_d.log
echo "== compare"
python $T/compare_all.py --out out 2>&1 | tee out/compare.log
