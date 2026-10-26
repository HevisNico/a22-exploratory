A22 — Fixed-gain controls and shuffled learned gains

Open report.html in a browser. All report text, figure labels and file names
are in English. The report embeds its figures and works offline.

Questions:
1. Can uniform gains fixed before the first source pulse transmit the word?
2. Does the assignment of learned gains matter beyond their distribution?

Protocol:
130 layers, 12 lanes, 128 irregular pulses, 20 network seeds at each of three
noise levels. The gain grid and shuffle definitions were fixed before these
results. A single deterministic quiet control is included for each condition.
Primary uniform grid: gains 0.3/0.6/0.9/1.2/1.4/1.6/1.8/2/2.5/3/4; gains frozen
from t=0, b initially0.08 with the original b-learning rule retained.
Fully frozen controls: b=1.1, noisy gains1.6/2/3/4, full quiet grid.
Recovery-time controls: b=0.08 fully frozen, gains2/4.
Learned baseline: provided normal2048-pulse learned gains and b, both frozen.
Shuffles: within layer; within layer and port; within layer after preserving
layers1–6. Two permutation draws per network seed. b stays at its learned cell.
New matched noise field: stage7001, labels2000000+i.
No seed selection or refinement of the gain grid after observing outcomes.

Replication unit: the network seed. Two shuffles of one seed are repeated
measurements, not two independent learned networks. Bootstrap analyses average
shuffle draws within each seed before resampling the twenty seeds.
A selected best grid point requires fresh tests for selection-adjusted claims.

Files:
report.html: complete report, including limitations and controls for b.
summary.json: groups and exploratory paired bootstrap intervals.
metrics.csv: per-realization measurements.
results/: raw output events, layer profiles, and freeze/shuffle diagnostics.
permutations/: exact scalar-gain permutation indices (NumPy .npz).
inputs/: learned checkpoints, including the documented repaired checkpoint.
PROTOCOL.json, VALIDATION.json, AUDIT.json: protocol and verification evidence.
INPUT_REPAIR.json: provenance of the earlier normal_2_9.states repair.
INPUT_HASHES.json, PROVENANCE.json: SHA-256 provenance.
src/: source, including the reference kernel and minimal freeze-gain change.

Reproduce (Python3, NumPy, Matplotlib, g++C++17):
g++ -O3 -std=c++17 -ffp-contract=off src/control.cpp -o control
python run.py
python analyze.py
python report.py
Existing completed results are reused. Move results/ to recalculate.
For validation:
g++ -O3 -std=c++17 -ffp-contract=off validation/reference/control.cpp -o validation/reference_control
python validate.py

The simulator is the supplied numeric point implementation. No certified engine
is used. Energy reserve E is not integrated. Gain sums are not energy costs.
A successful hand-set static network does not explain how those parameters can
be acquired autonomously from the nominal initialization. These finite tests do
not establish reliability for all future noise or arbitrary input families.
