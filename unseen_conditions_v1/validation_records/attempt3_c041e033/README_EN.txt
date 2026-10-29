Unseen conditions v1: validation attempt 3, PASS

The SAME rebuild_pr11 sandbox and existing build were used. No recompilation.
The first preparation stopped before validation because PR #12 was not merged.
Its original logs and STOPPED.json are included under logs/stopped_before_pr12/.
After explicit user authorization to resume, main was pulled to merge PR #12.
The source lock hash and byte equality to set_aside/SOURCE_LOCK.rebuild.json,
both executable hashes, worktree state, and both historical report hashes passed.
The current lock's validation directory was absent before launching validation.
check-registration passed, followed by ONE invocation of study.py validate.
It returned exit code 0 and produced a PASS report. No retry or correction.
No build, design, test, analyze, plan or unit test command ran during this request.

validation/ contains all three complete validation directories: the two old
failures, unchanged, and the new successful attempt. VALIDATION.json at the
archive root is a byte-identical copy of the new report; its hash is provided.
COMMIT.txt contains the full post-pull HEAD and its merge headline.
GIT_STATUS_AFTER.txt is the complete post-validation worktree status.
Only validation/ and the existing cc0xdGW0.s are untracked; tracked files are clean.
The build, .s temporary, and historical files remain unchanged in the sandbox.

Resumed execution logs record exact argv, cwd, UTC start, duration, exit code
and complete combined stdout/stderr, including empty output files.
COMPLETE_COMMAND_OUTPUT.txt combines every resumed command in order.
SHA256SUMS.txt covers every other regular file in this ZIP; as usual it does
not cover itself. Directory entries are included to preserve the full tree.

PASS concerns the registered validation checks. No adaptive-versus-static
design or held-out experiment was launched, and no performance claim follows.
