# Ablations of the learning rule at 130 layers (exploratory)

**Status: exploratory point simulations, not certified.** Five conditions × 20 seeds, plus three
noise-free controls. Ring of 12 lanes, 3 parents per cell, 130 layers. Fresh cells (gains 0.3, 1.2,
0.3; q = 0.1; b = 0.08). Training: 128 canonical pulses at times 8k on lane 0. Test: 24 irregular
pulses from time 4096, intervals 20 × (1, 1.1, 1.05, 1.2, 1, 1.15) repeated.

Noise: each pulse on each connection is multiplied by exp(0.1 Z − 0.005), Z standard normal (10 %
coefficient of variation, mean preserved), plus uniform centred jitter of standard deviation 0.03 on a
fixed delay of 0.1. Perturbations are paired across conditions by seed, layer, cell, port and label.

## Conditions

| Condition | Definition |
|---|---|
| Normal rule, noise from training | Gain learning only while the principal is READY (the A22 rule); noise during training and test |
| No learning | Gains and b fixed from t = 0 |
| Learning allowed under protection | Only the READY gate of gain learning is removed |
| Normal rule, noise at test only | Noise-free training, then noisy test |
| Learned under noise, then frozen | Normal rule and noise throughout; gains and b frozen at t = 4096 |

## Results at layer 130 (20 seeds each)

| Condition | Pulses recovered | Seeds with any output | Complete word on 12 lanes |
|---|---:|---:|---:|
| Normal rule, noise from training | 1.4 % (0 to 11 %) | 7 / 20 | 0 / 20 |
| No learning | 0 % | 0 / 20 | 0 / 20 |
| Learning allowed under protection | 54.2 % (33 to 68 %) | 20 / 20 | 0 / 20 |
| Normal rule, noise at test only | 0 % | 0 / 20 | 0 / 20 |
| Learned under noise, then frozen | 0 % | 0 / 20 | 0 / 20 |

Noise-free controls:

| Control | Pulses recovered at 130 | Complete words |
|---|---:|---:|
| Normal rule | 100 % | 12 / 12 lanes |
| No learning | 0 % | 0 / 12 |
| Learning allowed under protection | 92 % | 0 / 12 |

## Reading

- **No learning, no transmission.** With the nominal initial gains, a first-layer cell receives only
  its central port (gain 1.2) and its peak charge is about 0.769 < 1: the network never ignites, even
  without noise. Learning is therefore necessary here, but by construction of the initial state; this
  alone does not show what makes transmission robust.
- **The protection gate is needed for exact transmission.** Without noise, removing it still lets 92 %
  of pulses through, but no lane ever recovers a complete word.
- **With noise and only 128 training pulses, training does not reach layer 130.** In both noisy
  conditions with learning, no training pulse reached layer 130 in any of the 20 seeds. The failures in
  the first table therefore measure an unfinished installation of the regime, not the robustness of an
  installed one. This motivated the longer training in [`../noisy_training_130/`](../noisy_training_130/README.md).
- Learning allowed under protection transmits more under noise (54 % against 1.4 %), but never a
  complete word. Within this protocol, the results do not show that the gate is needed for robustness
  to noise.

Exact 95 % (Clopper–Pearson) intervals and paired bootstrap comparisons are in `summary.json`.

## Validation

The extended simulator reproduces the 21,302 historical events (maximum date error 3.1e-11). Analytic
checks of the gates: constant gain under protection with the normal rule, full 0.6 increment without the
gate, cap at 4, and effective freezing of gains and b (`VALIDATION.json`, `REFERENCE_RECHECK.json`).

## Files and replay

| Path | Content |
|---|---|
| `rapport.html`, `resultats.png` | Full report and figures (in French) |
| `summary.csv`, `summary.json`, `by_layer.json` | Metrics per run, intervals and comparisons, profiles by layer |
| Raw outputs (`ablations_130_output_part1.zip`, `_part2.zip`, 25 MB) | Emissions and states of every run: assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1); unzip both here |
| `kernel.py`, `kernel.diff`, `reference_kernel.py` | Simulator with the interventions, and its changes |
| `sources/` | Earlier campaign sources and the point simulator kit |

With Python 3, NumPy, SciPy and Matplotlib, from this folder:

```sh
unzip ablations_130_output_part1.zip && unzip ablations_130_output_part2.zip   # from the release
python3 build_kernel.py
python3 validate.py
python3 run.py --workers 8      # reuses existing results; move output/ away to recompute
python3 reference_recheck.py
python3 report.py
```
