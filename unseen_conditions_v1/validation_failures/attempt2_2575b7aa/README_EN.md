# A22 unseen_conditions_v1 — amendment 1 validation failure

The requested checks passed after merge PR #9. SOURCE_LOCK.json matches
2575b7aa8a76ca4c72f7d06a1f6c47b7e024ca07530a86ea057b06f76b3f87de.
The rebuild binaries still match 60f2a7d6... and 67aff94f.... Git status was
clean BEFORE copying failure 1 or launching the allowed commands.

The previous failure was copied to validation/ and its VALIDATION.json hash
matched cecb05e623926408e7771444cbe6617262c44f8195cb337a5ca65d2ee3fdcbbd.
check-registration passed. Exactly one validate command was executed after
amendment 1. It failed with: Rested static shortcut is not exact: static_00.
No correction or retry was performed. No design, held-out test or analyze
command was launched. Both failure directories are retained unchanged.

Contents:
- unseen_conditions_v1/validation/: COMPLETE directory, including restored
  failure 1 and all newly produced outputs, inputs, checkpoints and failure record
- unseen_conditions_v1/SOURCE_LOCK.json: current pinned source/binary lock
- logs/resumed_execution/: complete command output, exit codes, monotonic durations
- logs/pre_merge_preparation/: earlier stopped preparation, before the user merged PR #9
- VALIDATE_AMENDMENT1_FAILED_SUMMARY.json: outcome, timings, preservation checks, hashes
- COMMIT.txt: full checked-out commit SHA
- SHA256SUMS.txt: every payload file except itself

Start with logs/resumed_execution/COMMAND_OUTPUTS_FULL.log for commands 1–4
and the read-only post-preservation checks. Each original command also has an
individual log. The first preparation's initial lock check and checkout are
recorded separately; that preparation stopped at PR #8 and ran no validation.

All logs are outside the repository in the retained sandbox. The sandbox and
its build directory are left in place at:
/workspace/scratch/1ebdaa405a5d/rebuild_amendment1_pr8/a22-exploratory

This archive does not fix, rescore or reinterpret the failed numerical fixtures.
Tracked repository files and compiled binary bytes remain unchanged.
