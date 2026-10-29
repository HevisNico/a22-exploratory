Unseen conditions v1: DESIGN only, refused by existing phase lock

The same rebuild_pr11 sandbox was used. No compilation or git pull.
HEAD, source lock, both executables and the successful validation report had
the exact requested hashes. No tracked file had changed and runs/ was absent.
Preflight git status already showed an untracked RUNNING.lock.

ONE invocation of `python study.py design` was performed. It returned exit 2:
"Another phase is running, or an interrupted run needs manual audit."
The design routine refused the existing phase lock. The launcher wrote the
included runs/INCOMPLETE.json record. The lock was not removed or changed.
No retry, correction, test, analyze or selection_evidence.json creation.

runs/ is included COMPLETELY as it exists after this refusal. There is no
DESIGN_SELECTION.json, STATUS.json, CAMPAIGN_CLOCK.json, inputs/ or design/
because the design phase did not reach those steps. There is no selection
SHA-256 to provide. The 12-hour CAMPAIGN_CLOCK.json was not created.
No claim is made about whether another process or a stale lock caused this;
no process inspection or manual lock correction was performed.

COMPLETED_AT_UTC.txt gives the command completion time. The sandbox and build
remain intact. GIT_STATUS_AFTER.txt and RUNNING.lock are included as evidence.
Numbered command logs retain exact argv, cwd, UTC start, duration, exit code
and complete combined stdout/stderr. COMPLETE_COMMAND_OUTPUT.txt combines them.
SETUP_DIAGNOSTIC.json records an earlier failed read-only relative-path lookup.
SHA256SUMS.txt covers every other regular file in this ZIP, excluding itself.
