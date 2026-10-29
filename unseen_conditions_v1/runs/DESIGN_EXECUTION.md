# Design phase — execution record

- Executor: Claude, in its own session, for the author (see `incidents/design_refused_phase_lock/REVIEW.md`).
- State: main `b74c9bd6e64023653da5733bf908eb702237e28f`, `SOURCE_LOCK.json` `c041e033…`,
  `registration.json` `9cdfab3e…`, registered binaries `driver` `60f2a7d6…`, `driver_reference` `67aff94f…`
  (copied from the published rebuild, not recompiled), validation report `6d0bc76b…` (PASS).
- Preconditions checked: `check-registration` and the validation gate passed, no `runs/`, no `RUNNING.lock`,
  no tracked modification, review PR #14 merged (03:10:32 UTC).
- Command: `python study.py design`, once, Python 3.13.17, numpy 2.3.5, 4 workers.
  Started 03:11:14 UTC (campaign clock), finished 03:14:48 UTC, exit code 0; `RUNNING.lock` removed.
- Output: 384 design jobs, all `OK_POINT_NOT_CERTIFIED`; `DESIGN_SELECTION.json` SHA-256
  `c56d797ce270b807dda81d64463a8bd9dfcc43f5230e599157e5c0a5775d7b5b`, selected candidate 1.
  `DESIGN_COMMAND_OUTPUT.log` is the complete console output. No held-out input exists yet.
