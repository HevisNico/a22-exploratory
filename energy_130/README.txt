A22 — CORRECTED ENERGY AUDIT AND MATCHED RERUN

Open report.html for the self-contained English report.

What changed
1. Direct gate-on/off tests now start from exactly the same learned state.
2. Acquisition energy is measured on all 20 seeds at each noisy level.
3. Acquisition + held-out test is reported alongside test-only costs.
4. Local validation reconstructs physical state dynamics, threshold events,
   work rates and pump input independently from raw inputs.
5. Production pump input is integrated from its rate 10*(100-E), instead of
   being assigned as work plus reserve change.
6. Frozen-gain controls are explicitly secondary static-assignment tests.

The physical cost law was NOT changed. No general depleted-reserve solver
or E=0 experiment is claimed. Numerical results are not interval proofs.
All learned checkpoints were regenerated from nominal initial states.
Earlier archived checkpoints are used only by the optional regression check,
never as inputs to this corrected campaign.

Files
PROTOCOL.json                  Fixed campaign settings and comparison scope
src/                           Corrected C++ solver and fixture bridge
validate_independent.py         Independent Python hybrid state-equation oracle
VALIDATION.json, validation/    Local cross-check inputs and detailed outputs
training/                      122 regenerated acquisitions and terminal states
results/                       305 held-out tests and terminal states
metrics.csv                    Work, fidelity, gain motion and saturation
summary.json                   Paired bootstrap summaries and component deltas
AUDIT.json                     Full-campaign consistency checks
REGRESSION.json                 Optional comparisons with earlier local outputs
reference/                     Pinned original model reference and licenses
MANIFEST_SHA256.json            Artifact checksums (excluding the manifest itself)

Reproduce (Linux, g++, Python 3, NumPy, SciPy, Matplotlib)
  g++ -O3 -std=c++17 -ffp-contract=off src/fixture_bridge.cpp -o validation/fixture_bridge
  g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
  python validate_independent.py
  python run.py
  python analyze.py
  python report.py

run.py uses 8 workers and only reuses outputs matching the exact executable,
protocol and initial-checkpoint hashes. For a completely fresh run, move
training/ and results/ aside and recreate those two empty directories.
Historical regression is optional: python regression.py, requiring the old
energy_experiment folder beside this package. It is not needed to reproduce
the new scientific comparisons.

Interpretation
Negative paired work differences favor the gate-on branch, except for the
explicitly labeled frozen comparison (learned gains minus uniform gain 4).
Report cost together with output-word quality and recall. Lower gain motion
does not automatically mean lower total work. Quiet is one deterministic
case; bootstrap intervals are reported for the three 20-seed noisy groups.

All values use the source model's unit-cost convention, not measured joules.
Model source: https://github.com/HevisNico/a22-interval-replay
Pinned commit: 22294781127aa47628bb8a3270d5c5a758c31729
The included reference document retains its original language and license;
all new report text, code comments, plot labels and documentation are English.
