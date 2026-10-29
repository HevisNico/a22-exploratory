# A22 unseen_conditions_v1 — failed validation, retained unchanged

check-registration passed. Exactly one validate command was run and failed.
Failure: suffix_64, layer=45 lane=1, nonchronological continuation.
No correction, retry, design, held-out test or analyze command was performed.
The same sandbox and original build binaries are retained. All requested hashes
matched before validation and still match after it. Tracked files are unchanged.

The command writes validation fixtures under unseen_conditions_v1/validation/,
not runs/. No runs/ directory was created. This archive includes the complete
actual validation/ output, including the failure record, raw fixture outputs,
checkpoints, physical inputs and saved job metadata. If a runs/ directory exists
at packaging time it is included in full; its presence is recorded in the summary.

logs/COMMAND_OUTPUTS_FULL.log contains complete combined stdout/stderr and
measured monotonic elapsed seconds for commands 1–3. Individual command logs
and status records are also included. check-registration/validate timings are
listed in VALIDATE_FAILED_SUMMARY.json.

Environment deviation: /tmp does not exist in this execution environment. The
requested mv failed without moving the source lock. The same local lock was
then put aside outside the repository in validate_request_logs/SOURCE_LOCK.local.json.
Both commands and their durations are retained. The user subsequently accepted
this location.

The requested merge-PR-6 log and all lock/binary hashes were verified before
check-registration/validate. The additional git status instruction arrived
after validate had already been launched; that read-only check was performed
then and confirmed no tracked modification. It is not claimed to have occurred
before launch. No validation was restarted to change this ordering.

SHA256SUMS.txt covers every archived payload file except itself. No source,
input, checkpoint or validation result was altered to prepare this archive.
