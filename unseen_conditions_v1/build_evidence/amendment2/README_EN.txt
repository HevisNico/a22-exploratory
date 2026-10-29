Unseen conditions v1: build-only after PR #11

Fresh main clone and git pull. HEAD is the merge of PR #11.
All 24 source checks passed before and after compilation.
Only `python study.py build` was invoked as a study phase; it compiled both
C++17 drivers and created SOURCE_LOCK.json. No executable driver was launched.
No check-registration, validate, design, test, analyze, plan, or unit test ran.

The old tracked SOURCE_LOCK.json and registration.json were moved intact to
the sibling set_aside directory outside the repository. Registration was not
restored. The new sandbox and build directory are preserved for the next step.
The post-build worktree status is included verbatim. An assembly temporary
named cc0xdGW0.s appeared during compilation and remains untouched.

BUILD_HASHES.txt gives the new lock and both executable SHA-256 hashes.
logs/commands.json records exact argv, cwd, UTC start, duration and exit code.
Numbered logs contain complete combined stdout/stderr, including empty output.
COMPLETE_COMMAND_OUTPUT.txt combines those records and outputs in execution order.
The ZIP also includes both built executables. Its SHA256SUMS.txt covers every
other archive entry. No source code or tracked document was edited.
