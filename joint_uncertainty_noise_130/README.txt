A22 JOINT PHYSICAL UNCERTAINTY + LINK NOISE — ENGLISH PACKAGE

Read REPORT.txt, INTERPRETATION.txt and PROTOCOL.json first.
This package contains a completed small numerical pilot, not a mathematical
certificate or an exhaustive coverage of a continuous uncertainty box.

Design fixed before acquisitions
--------------------------------
Six new seeds, 3000–3005; four paired regimes:
  nominal_quiet, nominal_noisy, uncertain_quiet, uncertain_noisy.
Each regime learns from 2048 source pulses, then freezes its learned gains and b
and evaluates 128 independent test pulses, with and without 24 lateral decoys.
All 24 acquisitions and all 48 evaluations are retained. No simulator failures
occurred. Per-job statuses distinguish successful solver completion from a
successful model transmission; inspect TRAINING_OUTCOMES.json and PER_SEED.*.

For each seed, draw C, L_m, L_s, L_e and M independently for each cell and port,
uniformly in the relative interval +/-1e-4 around the nominal value. This one
physical realization is fixed throughout acquisition and both evaluations and
is shared by the quiet/noisy uncertain arms. FIELDS.json records the draws'
observed ranges and hashes; fields/ contains the exact physical parameter files.
Other physical constants and the initial state remain nominal as specified in
PROTOCOL.json. No initial-state uncertainty is claimed.

The nominal/uncertain noisy arms query the same deterministic latent noise
field; acquisition and test use disjoint stage keys 0 and 8001. Noisy amplitude
is lognormal with sigma=.05, centered to mean 1; jitter is centered uniform with
standard deviation .015 on a fixed delay .1. Divergent physical trajectories can
query different downstream labels/occurrences: the latent field is paired, not
an externally forced identity of all realized downstream pulse trains.

Primary reporting criteria were fixed before acquisitions: source transmission,
complete words, extra outputs and relative interval timing error. Full definitions
are in PROTOCOL.json. Invalid interval pairs are never assigned zero timing
error; their count and the transmission failures are retained. Timing additions
and removals are paired measurements, not an exact causal label of false spikes.
Nominal quiet references are identical across seeds; the six logical rows do not
create six independent nominal quiet devices.

Contents
--------
REPORT.txt / INTERPRETATION.txt: findings and explicit limits.
PROTOCOL.json / AMENDMENT_BEFORE_ACQUISITIONS.json: frozen rules and user criteria.
PER_SEED.* / PAIRED_DECOY.* / PAIRED_FACTORIAL_CONTRASTS.*: all descriptive results.
SUMMARY.json / TRAINING_OUTCOMES.json / STATUS.json / PLANNED_JOBS.json: full accounting.
fields/ / FIELDS.json: exact physical realizations, shared across arms and stages.
results/: acquisition outputs, frozen checkpoints, event outputs and job statuses.
src/ / bin/: generalized per-port solver and Linux executables.
checks/: 12 independent ODE comparisons and 2 exact nominal-network regressions;
         the initial checker cap-detection correction is documented there.
SOURCE_LOCK.json: protocol, source, runner, checker and executable hashes at launch.
MANIFEST_SHA256.json: package content hashes.
reference/REFERENCE_INPUT.zip: the unchanged user-supplied earlier diagnostic,
                              included for the two nominal regression references.

Reproduction and analysis
-------------------------
Python 3, NumPy, SciPy and g++ with C++17 are needed for checks and compilation.
The completed data can be analyzed without running any simulation:
  python3 analyze.py
To compile the supplied generated sources, use from this directory:
  g++ -O3 -std=c++17 -ffp-contract=off src/train.cpp -o bin/train
  g++ -O3 -std=c++17 -ffp-contract=off src/evaluate.cpp -o bin/evaluate
  g++ -O3 -std=c++17 -ffp-contract=off src/bridge.cpp -o bin/bridge
restore_reference.py safely restores the earlier diagnostic beside this directory;
it does not simulate. verify.py then runs its local ODE and nominal regression
checks and prepares deterministic fields. Preserve the complete original package
before any replay. pilot.py run refuses to overwrite existing acquisition results;
for a fresh full replay, work in a copy with an empty results/ directory and rerun
verification before execution. No broad campaign is ever invoked by these scripts.

Numerical domain
----------------
The original regenerated-auxiliary finite pulse domain and positive continuous
reserve bound remain enforced. Nine work integrals are computed; detailed E and
pump trajectories are omitted and marked null. Parameter-specific durations are
computed from their drain rates, never held at nominal values under uncertainty.
No subthreshold-auxiliary, overlapping-port or resource-depleted simulation is
silently substituted. A simulator refusal would remain a separate recorded failure.
Source model commit: 22294781127aa47628bb8a3270d5c5a758c31729.
