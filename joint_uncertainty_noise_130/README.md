# Joint parameter uncertainty and link noise at 130 layers — exploratory pilot

**Status: completed exploratory point simulations; six seeds, not certification.**
The pilot combines fixed physical heterogeneity with temporally varying link noise
during both learning and evaluation. All **24 acquisitions and 48 evaluations**
are retained. The recorded simulator-failure count is zero.

## Main result

At relative parameter uncertainty **±0.01% (ε = 1e-4)** and low link noise, all
six uncertain/noisy devices learned and then transmitted the entire 128-pulse
word exactly once and in order on every output lane of layer 130 **without decoys**.
Their mean relative interval RMS error was **0.497467%**. With 24 full-amplitude
lateral decoys, **3/6** complete network words remained perfect. High pulse
coverage therefore coexists with imperfect rejection of spurious inputs.

| Physical parameters / link noise | Test | Complete network words | Once-only ordered source coverage | Mean relative interval RMS |
| --- | --- | ---: | ---: | ---: |
| Nominal / quiet | Baseline | 6/6¹ | 100% | about 4e-12% |
| Uncertain / quiet | Baseline | 6/6 | 100% | about 4e-12% |
| Nominal / noisy | Baseline | 6/6 | 100% | 0.518236% |
| Uncertain / noisy | Baseline | **6/6** | **100%** | **0.497467%** |
| Nominal / quiet | With 24 lateral decoys | 6/6¹ | 100% | 0.000577% |
| Uncertain / quiet | With 24 lateral decoys | 6/6 | 100% | 0.000577% |
| Nominal / noisy | With 24 lateral decoys | 3/6 | 99.934896% | 0.594276% |
| Uncertain / noisy | With 24 lateral decoys | **3/6** | **99.967448%** | **0.504225%** |

**Effect of the decoys** (paired contrast, decoy test against baseline test of the same learned
state, mean over six seeds; from [PAIRED_DECOY.json](PAIRED_DECOY.json)):

| Physical parameters / link noise | Output events added by the decoys | Output events removed |
| --- | ---: | ---: |
| Nominal / quiet | 0 | 0 |
| Uncertain / quiet | 0 | 0 |
| Nominal / noisy | 8.500 | 1.500 |
| Uncertain / noisy | 8.833 | 0.500 |

These numbers describe the difference between the two tests, not errors of either test.
`REPORT.txt` and `SUMMARY.json` (kept byte-identical to the release asset) print this per-regime
contrast on both the baseline and the decoy row; read it as above.

¹ The nominal quiet network and its inputs are identical across seeds; these are
repeated references for pairing, not six independent nominal quiet devices.
Numerically negligible quiet timing errors are floating-point residuals, not an
additional proof of exact timing. RMS values are means of the six network RMS
values, and only valid adjacent-source pairs enter those values.

## Fixed design

- **Network:** 130 feedforward layers × 12 lanes; source on lane 0; gate-on model.
- **Six new seeds:** 3000–3005; four paired regimes, nominal/uncertain × quiet/noisy.
- **Physical uncertainty:** independent uniform relative draws in [-1e-4, +1e-4]
  for C, L_m, L_s, L_e and M, per cell and port. Each device's draw is fixed during
  acquisition and both evaluations, and shared by its two uncertain regimes.
- **Unchanged quantities:** a, κ, r, r_m, actuation gains, b_max, pump and initial
  states remain nominal. This pilot does not include the initial-state box δ.
- **Noise:** lognormal pulse amplitude, mean one and log standard deviation 0.05;
  centered uniform jitter, standard deviation 0.015, around mean link delay 0.1.
  Nominal/uncertain noisy regimes share a counter-based latent noise field.
  Acquisition and test use disjoint stage keys. Divergent traffic can query
  different downstream keys; realized pulse trains are not forced to coincide.
- **Learning:** 2,048 source pulses at spacing 8, with no seed selection.
- **Two evaluations per learned state:** 128 pulses with gaps repeating
  20, 22, 21, 24, 20, 23, once without decoys and once with 24 lateral decoys.
  Gains and b are frozen in both tests; q is reset to r = 0.1 as declared in the
  protocol. The finite regenerated-auxiliary pulse domain remains enforced.

The two evaluations are **baseline and decoy tests**, not active/frozen-plasticity
comparisons. See [PROTOCOL.json](PROTOCOL.json) and the amendment recorded before
acquisitions in [AMENDMENT_BEFORE_ACQUISITIONS.json](AMENDMENT_BEFORE_ACQUISITIONS.json).

## Interpretation and limits

The useful finding is joint operation under these sampled conditions. The small
timing difference between nominal/noisy and uncertain/noisy is not evidence that
uncertainty improves performance. Six physical draws do not cover the parameter
box, and individual pulses or lanes are not independent network replicates.

In the noisy mixed test, some words fail because of extra or missing/ambiguous
outputs even though source coverage is high. Passive tags are not complete
residual-charge causal histories. Paired timing additions/removals can include
displaced events and must not automatically be called causally identified false
spikes. Inspect [PER_SEED.csv](PER_SEED.csv) and [PAIRED_DECOY.csv](PAIRED_DECOY.csv).

Only one nonzero noise level is tested. Quiet/noisy changes both acquisition and
test noise; this is a total-regime comparison. No gate-off or hybrid control is
included, and no superiority of the gate or lifecycle energy advantage follows.
Nine model-work integrals and a positive reserve bound are recorded; detailed E
and pump trajectories are not integrated. These point simulations do not extend
the interval proof or establish a hardware result.

Read the original [REPORT.txt](REPORT.txt) and [INTERPRETATION.txt](INTERPRETATION.txt)
for the numerical findings and qualifications.

## Data, sources and validation

| Material | Location |
| --- | --- |
| Protocol, accounting, physical-field ranges | `PROTOCOL.json`, `STATUS.json`, `PLANNED_JOBS.json`, `FIELDS.json` |
| All seed-level metrics and paired contrasts | `PER_SEED.*`, `PAIRED_DECOY.*`, `PAIRED_FACTORIAL_CONTRASTS.*`, `TRAINING_OUTCOMES.json` |
| Summary and interpretation | `SUMMARY.json`, `REPORT.txt`, `INTERPRETATION.txt` |
| Solver sources and analysis scripts | `src/`, `analyze.py`, `scoring.py`, `pilot.py`, `verify.py` |
| Recorded local ODE checks and nominal regressions | `checks/` |
| Raw training/test outputs, exact physical fields, checkpoints, executables and regression inputs | Complete Release archive below |

The supplied validation records report 12 independent local ODE comparisons
(maximum state/event discrepancy about 1.06e-13) and two exact nominal-network
regressions. The checker correction is retained in `checks/ORACLE_CORRECTION.txt`.
These are local numerical checks and regressions, not a proof for every trajectory.
The generation scripts `build_sources.py` and `make_drivers.py` are kept as
provenance; `build_sources.py` rewrites the protocol, so it is not a replay step
for the frozen completed pilot.

The complete archive is a byte-identical copy of the supplied pilot package:

- **[Download A22_joint_parameter_uncertainty_and_noise_pilot_EN.zip](https://github.com/HevisNico/a22-interval-replay/releases/download/exploratory-data-1/A22_joint_parameter_uncertainty_and_noise_pilot_EN.zip)** from
  [Release `exploratory-data-1`](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1).
- Size: **8,557,405 bytes**.
- SHA-256: `6c7bf44e7b84c8f0486849bb177dfa20e7d2f17bf901e8e8c374bf44a6d97975`.
- Internal directory: `A22_joint_parameter_uncertainty_and_noise_pilot_EN/`.

## Recheck without launching training

From this repository directory, with Python 3 standard library only:

```bash
python3 check_release_asset.py
python3 check_release_asset.py /path/to/A22_joint_parameter_uncertainty_and_noise_pilot_EN.zip
```

The first command checks the published folder's hashes. The second also checks
the exact archive, its original 167-entry manifest, source locks, the expected
24/48 outputs, and checkpoint/field provenance. It never loads the bundled
binaries or starts a simulation. It is an integrity/accounting check, not an
independent numerical or mathematical validation.

To recompute metrics, extract the complete Release archive in a separate working
directory, enter `A22_joint_parameter_uncertainty_and_noise_pilot_EN/`, and run:

```bash
python3 analyze.py
```

This re-reads stored outputs and rewrites generated reports and CSV/JSON metrics;
preserve a pristine extraction if you want to compare the original hashes.
It runs no learning. For solver-check replay, use a second working copy:

```bash
python3 restore_reference.py
python3 verify.py
```

The latter requires NumPy, SciPy and compatible Linux executables (or a C++17
compiler to rebuild the three supplied generated sources as described in
[README.txt](README.txt)). It re-runs local checks and two nominal evaluations,
and regenerates fields/source locks. No fresh pilot is required to inspect the
completed data. A new full pilot would require an empty `results/` in a working
copy and explicit `python3 pilot.py run`; that is not part of these read-only checks.

Source model snapshot: `22294781127aa47628bb8a3270d5c5a758c31729`.
The archived protocol, sources, results and original manifest are preserved
unchanged. This GitHub README and the publication checker are additional packaging.
Repository licensing applies: code MIT; documents and data CC BY 4.0.
