# Held-out test and analysis — execution record

- Executor and state as in `DESIGN_EXECUTION.md` (main `b74c9bd6…`, lock `c041e033…`, registered binaries).
- `selection_evidence.json` written after the design selection was merged by PR #16 (merge commit
  `cde775c2b05edeb107f92993632c770f8ab7e833`); SHA-256 `e7062d4a…`. No held-out input existed before.
- `python study.py test`, once: 03:17:13 → 04:03:33 UTC, exit code 0, 128/128 contexts, 1 952 jobs,
  0 simulator refusals, 0 unavailable acquisitions; inside the 12-hour campaign clock (started 03:11:14).
- `python study.py analyze`, once, exit code 0. Results in `analysis/` (`RESULTS_EN.md`, `SUMMARY.json`).
- Raw held-out outputs and inputs (`runs/test/`, `runs/inputs/`, 6 264 files, 497 MB) are listed with
  SHA-256 and size in `TEST_AND_INPUTS_MANIFEST.json`; they are published as the release asset
  `A22_unseen_conditions_v1_runs_test_inputs.zip` (SHA-256
  `059777bc5396515f10e8966291e087ffd4e7ce976ebcc238e1db25103eba2aeb`).
