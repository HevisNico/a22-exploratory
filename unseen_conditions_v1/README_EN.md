# A22 held-out conditions — code kit

**Code prepared only. No numerical validation, design search or held-out
simulation has been run. No registration evidence has been supplied.**

Read PROTOCOL.md and IMPLEMENTATION_NOTES.md before using this kit. The protocol
is English, and the original kernel and license are retained. This is a point
simulator experiment, not a certified interval calculation or hardware result.

## Contents

| File | Purpose |
|---|---|
| driver.cpp | Matched adaptive/static simulator and diagnostic entry point |
| vendor/ | Kernel with documented actuation and checkpoint-clock changes |
| reference_vendor/ | Untouched published kernel for deferred parity checks |
| config.py | Fixed cohorts, conditions, candidates and deterministic generators |
| study.py | Explicit, gated build/validation/design/test/analysis phases |
| scoring.py | Independent event-to-word scoring and accounting checks |
| inference.py | Exact device sign test and paired device bootstrap |
| validation.py | Numerical fixtures, blocked until registration is documented |
| analysis.py | Complete job ledger, per-device/per-word results and interpretation |
| test_gates.py | Software gate tests; no model simulation |
| registration.example.json | Unfilled evidence template; deliberately blocks execution |
| selection_evidence.example.json | Evidence for committing design selection before test |

## Preparation without simulations

Use Python 3.12, a C++17 compiler (g++), and NumPy 2.3.5 for final inference.
An existing compatible Python environment is sufficient; no dependency download
is triggered by the code. From this directory:

```sh
python study.py --help
python study.py plan
python -m unittest test_gates.py
python study.py build
```

These commands do not run a model, generate physical fields or choose a static.
Build compiles the modified and reference drivers and creates SOURCE_LOCK.json.
If included, BUILD_VERIFICATION.json records preparation checks only.
Any code change requires a new build and a new reviewed implementation record.
Build refuses a directory with registration evidence or study runs: use a fresh
working copy, retaining earlier evidence/results.

## Registration gate — not completed by this kit

The protocol's reviewed main-branch PR, protected tag and main protections must
exist before simulation. An external published timestamped deposit is recommended.
Review the implementation detail about static per-port caps in
IMPLEMENTATION_NOTES.md before registering this implementation.

Only once those steps are actually completed, copy registration.example.json
to registration.json and fill it with the real evidence and exact hashes.
The protocol SHA-256 is the hash of PROTOCOL.md; source_lock_sha256 is the hash
of SOURCE_LOCK.json. Author-entered commit dates and invented boolean flags are
not timestamp proof. The launcher checks local consistency, not the truth of
remote evidence. A reviewer must inspect the actual public records.

```sh
python study.py check-registration
```

With the supplied unfilled template, validation/design/test remain blocked.
Nothing automatically publishes a PR, tag, branch, deposit or protection setting.

## Later execution — explicit separate commands

The following commands launch scientific calculations and are **not** part of
code preparation. Do not run them until their prerequisite gates are completed:

```sh
python study.py validate
python study.py design
```

Validation uses dedicated fixtures only. If validation fails, stop and preserve
the failure record; a public prospective amendment is required before retrying.
Design evaluates all 12 candidates on 8 separate design devices and writes
runs/DESIGN_SELECTION.json. Commit that selection and all design results, then
copy selection_evidence.example.json to selection_evidence.json and enter its
real commit, public evidence URL and exact selection/source-lock hashes.

```sh
python study.py test
python study.py analyze
```

Only after the selection gate passes are any of the 32 held-out device fields
generated. Each arm reads the same physical and H files and latent test-noise
keys. No state is reset between the four test words. Analysis independently
recomputes saved event scores and emits the full job ledger, PER_WORD.csv,
PER_DEVICE.json, paired-H checks, SUMMARY.json and RESULTS_EN.md.

The primary comparison is active learning versus the one design-selected static.
The hindsight oracle is a diagnostic finite-family envelope, not a deployable
generalization result. Bootstrap resamples whole devices. Refusal sensitivity
must preserve a positive result before any adaptive-advantage claim is allowed.

## Faults, interruption and preservation

All jobs have fixed IDs, inputs and output hashes. Completed jobs can be reused
only if their bindings match. Never delete unsuccessful jobs or partial files
to obtain a fresh result. A timeout, execution/integrity fault or 12-hour limit
creates an incomplete-study record and blocks inference; review prospectively.
The wall-clock limit includes waiting between design and test.

RUNNING.lock prevents simultaneous phases. After an interrupted process, first
verify that no child simulator remains active and audit partial outputs. Do not
remove the lock merely to start a duplicate campaign. Do not invoke the
low-level binaries directly to bypass a registration or selection gate.

## Archives and reproduction

Each delivered ZIP is an ordinary independent archive below 30,000,000 bytes.
If several numbered ZIPs are supplied, extract every part into the same folder.
Verify the delivery SHA256SUMS.txt before use. Linux executables are convenience
copies; a fresh source build is needed on another platform and has its own
reviewed build/source-lock identity. No study results are bundled or fabricated.

Software: MIT, see LICENSE. Documentation licensing: LICENSE-docs.md. Kernel
basis: HevisNico/a22-exploratory at 211584f0355903f952d410165aa455c2b27390ba.
Prepared with AI assistance; compilation is not numerical or specialist review.
