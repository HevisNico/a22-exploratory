A22 — DIRECTIONAL SELECTIVITY

Open report.html for the English report. Original model reference and license
documents retain their original language and attribution in reference/.

Design
6 configurations x7 scenarios x(3 noise levels x20 seeds +1 quiet case)=2562.
Both gains and b are frozen. All conditions use the same paired probe list.
Uniform4, uniform2 and the median controls match normal learned b cell by cell.
The ungated-trained policy retains its own learned b. Static median values were
chosen exclusively from training checkpoints before the probe campaign.

Two primary endpoints
1. Fraction of probe identities reaching any output at layer 130, including
   mixed contamination. Twenty-four injected probe identities per trial.
2. Fraction of true lane/identity pairs recovered exactly once and purely,
   plus full true-word success and ordering.

Complementary diagnostics distinguish mixed contamination from false-only
emissions and from inclusive true delivery. Inclusive true delivery allows
one probe-contaminated output carrying exactly one true identity, with no
duplicate occurrence of that identity. These are additional descriptive
analyses of the same outputs, not altered experiments.

Important geometry control
Initial gains were(0.3,1.2,0.3), so directional bias is present before learning.
This campaign does not demonstrate discovery of direction from isotropic gains.
A homogeneous central-strong/lateral-weak network may fail to distribute the
single-lane source to all 12 required outputs. The additional median-rule-after-
layer 6 configuration preserves the learned entrance and tests the simple rule
only in the fully reached interior. Do not interpret entrance failure alone
as proof of a sophisticated learned interior.
The hybrid control retains learned entrance gains AND the learned b profile;
it is not an entirely hand-specified network independent of learning.

Files
PROTOCOL.json        Predeclared settings, primary endpoints and joint rule
CALIBRATION.json     Frozen median values and input checkpoint hashes
inputs/              122 copied training checkpoints, no relearning in tests
results/             2562 raw tests, final event provenance, layer rates, costs
src/                 Physical kernel plus passive provenance instrumentation
VALIDATION.json      Local checks and full-network clean regression
AUDIT.json           Whole-campaign checks and independent output recounts
metrics.csv          Per-seed work, filtering, fidelity and distortion
summary.json         Means, paired bootstrap intervals and layer profiles
report.html          Self-contained English report with embedded figures
MANIFEST_SHA256.json Archive content checksums

Reproduce (Linux, g++, Python3, NumPy, Matplotlib)
  g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
  g++ -O3 -std=c++17 -ffp-contract=off src/unit.cpp -o validation/unit
  python validate.py
  python run.py
  OPENBLAS_NUM_THREADS=1 python analyze.py
  OPENBLAS_NUM_THREADS=1 python report.py

validate.py performs historical regressions when the previous energy_corrected
folder is present beside this package; see validation script for a standalone
mode. The archive retains those observed regressions. Existing completed tests
are reused only when executable, protocol, calibration and input hashes match.

Limitations
The specified median control is not a proven optimal static rule. Probe noise
is sparse pulse noise, not arbitrary continuous noise. Provenance unions track
active raw pulses at firing, not exact counterfactual causality of residual q.
The primary strict recall measures uncontaminated delivery; inspect inclusive
delivery before calling every mixed event a physically lost true signal.
Aggregate layer profiles are recorded; individual disappearance histories were
not retained. Numerical point simulations are not certified interval proofs.
The positive-E domain is checked; E=0 behavior is not tested.

Model source: https://github.com/HevisNico/a22-interval-replay
Pinned commit: 22294781127aa47628bb8a3270d5c5a758c31729
