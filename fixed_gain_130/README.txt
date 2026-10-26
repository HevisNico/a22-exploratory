A22 - Fixed maximum-gain controls (English edition)

Start with A22_fixed_gain_controls_report.pdf.
The archive contains the English report, English protocol and documentation,
raw numerical results, validation checks, source code, and reference checkpoints.

QUESTION
Can the previously observed deep noisy transmission be obtained by choosing
high gains in advance, without gain learning or any parameter learning?

DESIGN
130 layers; 12 lanes per layer; seeds 0-19; three noise levels.
Log-amplitude standard deviation: 0.05,0.10,0.15.
Arrival-jitter standard deviation: 0.015,0.030,0.045; nominal delay 0.1.
Conditioning: 2,048 source impulses at intervals 8, without outcome-based selection.
Primary held-out test:128 impulses, irregular intervals 20-24.
Secondary tests:24 impulses, and a separately held-out faster rate with
irregular intervals 8-9.6. The faster tests were declared before new outcomes.

NEW CONTROLS
fixed_all: all gains 4 and b=0.08 from time zero, fixed throughout.
fixed_all_max_b: all gains 4 and b=1.1 (the existing upper limit) from time zero,
fixed throughout. This secondary control avoids penalizing a fixed design with
slow nominal recovery when evaluating faster source rates.
fixed_gain: all gains 4 from time zero, fixed throughout; b starts at 0.08 and
retains the original local update. Test copies keep b active or freeze it.

REFERENCE CONDITIONS
normal: preceding noisy training with the local READY cutoff.
ungated: preceding noisy training without the gain-learning READY cutoff.
The reference_campaign/output directory includes unmodified preceding runs and
learned checkpoints. One incomplete checkpoint serialization was restored from
its complete matching JSON states; the recovery audit is included. They are
reused matched references, not new independent
seeds. The earlier French report is not included in this English archive.

INTERPRETATION
A complete output word requires every source label exactly once, in order,
on every one of the 12 output lanes, with no extra events. Recall counts exact
single occurrences; duplicates are not successes. Timing RMS is conditional
on recovered consecutive labels and does not replace the loss metrics.
The random field is paired across compared conditions at a given source rate.
Train, primary test, and faster test have different random-stage identifiers.
The independent statistical unit is the seed, not a lane or impulse.

CONTENTS
PROTOCOL.json: protocol fixed before the new network outcomes.
summary.json: group estimates and paired statistical comparisons.
results.csv: layer 130 endpoints for every matched test and seed.
training.csv: conditioning diagnostics and parameter statistics per seed.
output/: new raw layer profiles, final output event trains, and checkpoints.
reference_campaign/output/: original paired reference runs and checkpoints.
VALIDATION.json: local Python/native solver comparisons.
AUDIT.json: fixed-parameter checks and independent final-output recounts.
validation/: exact network regression and independent Python propagation.
PROVENANCE.json: SHA-256 hashes of sources and raw outputs.
ENVIRONMENT.json; requirements.txt: computation environment.
*.diff: source changes relative to the preceding point simulator.

REPRODUCE
Requires Python 3 and g++ supporting C++17. Install requirements.txt if needed.
From the extracted folder:
  python build.py
  python validate.py
  python run_campaign.py --workers 8
  python analyze.py
  python report.py
The script reuses complete cached files. Move output/ to recompute the new
controls; retain reference_campaign/ for the learned reference states.
Run python validate_network.py after the first primary fixed_all dataset exists.

AUDIT NOTES
No gain or recovery value was chosen using held-out results. The fixed values
are the nominal b and the existing model upper bounds. No seed is excluded.
Frozen learned tests use independent copies, with no online parameter updates.
The original point simulator is used; there is no certified or interval engine.
Permanent stopping under arbitrary future noise is not established. Parameter
magnitudes are measured, while energy and hardware cost are not measured.
