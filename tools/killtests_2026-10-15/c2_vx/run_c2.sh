#!/usr/bin/env bash
set -euo pipefail
T=tools/killtests_2026-10-15/c2_vx
mkdir -p out data
echo "== freeze check"
sha256sum $T/PREREG.md $T/run_c2.py $T/verify_c2.py $T/fetch_c2.py $T/synth_c2.py $T/selftest_c2.py $T/compare_c2.py tools/killtests_2026-10-15/kt.py tools/killtests_2026-10-15/cal.py | tee out/frozen_as_run_c2.sha256.txt
cat $T/FROZEN.sha256 | tee -a out/frozen_as_run_c2.sha256.txt
for f in PREREG.md run_c2.py verify_c2.py; do
  want="$(grep " $T/$f\$" $T/FROZEN.sha256 | awk '{print $1}')"; have="$(sha256sum $T/$f | awk '{print $1}')"
  if [ "$want" != "$have" ]; then echo "::error::$f differs from the freeze record"; exit 1; fi
done
echo "freeze record verified" | tee -a out/frozen_as_run_c2.sha256.txt
echo "== self-test"; python $T/selftest_c2.py 2>&1 | tee out/selftest_c2.log
echo "== fetch"; python $T/fetch_c2.py --data data 2>&1 | tee out/fetch_c2.log
echo "== run"; python $T/run_c2.py --data data --out out 2>&1 | tee out/run_c2.log
echo "== verify"; python -I $T/verify_c2.py --data data --out out 2>&1 | tee out/verify_c2.log
echo "== compare"; python $T/compare_c2.py --out out 2>&1 | tee out/compare_c2.log
