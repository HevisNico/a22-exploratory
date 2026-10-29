# Review — design refused by a stale phase lock (no design job run)

Recorded prospectively, before any design job. No source, lock, registration or criterion changes.

## What happened

At 03:00:21 UTC the single `python study.py design` call (source lock `c041e033…`, main `b74c9bd6…`)
stopped after 0.075 s: `Another phase is running, or an interrupted run needs manual audit.`
`RUNNING.lock` was already present. As the launcher does for any stopped design phase, it wrote
`runs/INCOMPLETE.json` (SHA-256 `bc9fa911…`). No design input, job, clock
(`CAMPAIGN_CLOCK.json`) or selection was created. The complete record is in `archive/`.

## The lock

`RUNNING.lock` (SHA-256 `3b211714…`) reads
`{"phase": "validation", "pid": 5, "started_at": "2026-10-29T02:52:19.624458+00:00"}`: it is the
lock taken by the validation run of attempt 3 (started 02:52:19.58, report started 02:52:19.63).
`phase_lock` removes it in a `finally` block, and that run exited with code 0. The attempt-3 logs
(`validation_records/attempt3_c041e033/logs/resumed_execution/21.log`) show `git status` at
02:52:30.83, right after validation, with no `RUNNING.lock`; the design preflight at 02:59:54
(`archive/logs/03.log`) shows it present. The file therefore reappeared between the two sessions,
outside `study.py` — most likely a restore of the execution sandbox to a state captured during the
validation run. The cause cannot be established from the records; no study process was running,
and nothing in `runs/` existed before the refusal.

## Decision

The refusal is an environment fault, not a study outcome, and the 12-hour clock never started.
Before the single design call is repeated:

1. confirm that no `study.py` process is running (see the addendum below for how);
2. move `RUNNING.lock` and `runs/` (containing only `INCOMPLETE.json`) out of the repository,
   unchanged, after checking the two hashes above;
3. check every lock, binary and validation hash again, then run `python study.py design` once.

If the lock or anything else unexpected reappears, stop again; no automatic retry.

## Addendum — process check

A first resumption stopped at step 1 before touching anything (`resume_stopped_process_check/`):
the execution sandbox has no `/proc`, so `ps` cannot list processes (`Error, do this: mount -t proc
proc /proc`). Nothing was mounted. Step 1 is replaced by checks that do not need a process table:
the attempt-3 orchestrator recorded the validation process as exited (code 0 after 11.2 s,
`EXECUTION_RESULT.json`), its report records `completed_at` 02:52:30.80, and nothing under
`validation/` or `runs/` may have changed since then (every validation file hash listed in the
report and the two hashes above are checked again). Steps 2 and 3 are unchanged.
