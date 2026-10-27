# Longer noisy training at 130 layers (exploratory)

> **Correction (25 October 2026).** In this study, the noise generator reused, for some pulses of the
> **24-pulse test**, the noise keys of training pulses from label 128 onward: part of that test saw the
> same noise draws as training pulses. The 24-pulse results below are therefore not a fully independent
> test. The 128-pulse test used separate keys. The follow-up study
> [`../gate_noise_130/`](../gate_noise_130/README.md) uses separate keys for every evaluation and
> confirms the main effect at three noise levels (with gains frozen at test, noisy training beats clean
> training by 21 to 91 points). It also tests the protection gate: it is **not** needed for this
> robustness.

**Status: exploratory point simulations, not certified.** 20 seeds, paired controls.

The ablation study (`../ablations_130/`) showed that with noise, 128 training pulses do not let the
training reach layer 130. Here, noisy training continues until it does, and the learned networks are
then tested on independent noisy pulse words.

## Protocol

Ring of 12 lanes, 3 parents, 130 layers, nominal physical parameters, fresh cells (gains 0.3, 1.2,
0.3; q = 0.1; b = 0.08). Canonical training pulses on lane 0 every 8 time units. Noise on every
connection and pulse: amplitude × exp(0.1 Z − 0.005) (10 % coefficient of variation), plus uniform
centred jitter of standard deviation 0.03 on a mean delay of 0.1.

**Stopping rule, fixed before any test:** try 512 training pulses, then 1,024, then 2,048 if needed.
Stop when the last 64 source labels are each recovered exactly once on all 12 output lanes, with no
ambiguous emission in that window. The decision uses training data only; no seed is excluded.
Outcome: 17 seeds stopped at 512 pulses, 2 at 1,024, 1 at 2,048 (`PREPARATION_AUDIT.json`).

**Tests**, each from an independent copy of the learned state: a 24-pulse word and an independent
128-pulse word, intervals 20 × (1, 1.1, 1.05, 1.2, 1, 1.15) repeated, same noise laws, fresh random
draws. Each test is run with learning active and with gains and b frozen.

**Control:** for each seed, training without noise for the same number of pulses, then the same noisy
tests.

## Results at layer 130 (20 seeds)

| Training / test | Pulses recovered | Complete word on all 12 lanes | 95 % CI (complete word) | Relative RMS interval error |
|---|---:|---:|---:|---:|
| **24-pulse word** | | | | |
| Noisy training, learning active | 100 % | 20 / 20 | [83.2 %, 100 %] | 0.99 % |
| Noisy training, frozen | 100 % | 20 / 20 | [83.2 %, 100 %] | 0.99 % |
| Clean training, same duration | 85.2 % (78 to 90 %) | 0 / 20 | [0 %, 16.8 %] | 7.27 % |
| **128-pulse word** | | | | |
| Noisy training, learning active | 99.93 % | 16 / 20 | [56.3 %, 94.3 %] | 1.05 % |
| Noisy training, frozen | 99.96 % | 17 / 20 | [62.1 %, 96.8 %] | 1.04 % |
| Clean training, same duration | 96.4 % | 0 / 20 | [0 %, 16.8 %] | 3.62 % |

Over the 30,720 expected responses of the long test, learning active: 12 missing labels and 8
duplicated; frozen: 12 missing, 0 duplicated.

## Reading

- **Noise during training is what makes the difference.** Same duration, same test noise: 20/20
  complete words after noisy training, 0/20 after clean training.
- **The robustness is stored in the learned state.** Freezing gains and b during the test gives the
  same results: it is not an on-line repair.
- **Transmission is reliable, timing is approximate.** With 10 % amplitude noise, intervals are
  preserved to about 1 % RMS, not exactly.
- **Not established here:** other topologies or physical-parameter uncertainty; any guarantee
  beyond these 20 seeds. Twenty successes out of twenty still give only an 83 % lower bound (95 %
  confidence) on the probability of a complete word.

## Validation

- The Python kernel is the ablation kernel, already checked against the 21,302 historical events; the
  only change is the observation date.
- The training/test split is checked against an uninterrupted simulation (seed 0, 128 pulses): maximum
  date error 3.8e-11, gain error 1.2e-10 (`SPLIT_VALIDATION.json`).
- A C++ translation (`point_cell.cpp`) accelerates the point loop only. It matches the Python simulator on
  12 local cases and on the full 512-pulse training and four tests of seed 0: maximum date error 2.6e-10,
  gain error 3.5e-9 (`NATIVE_VALIDATION.json`). It is not the certified engine.

## Files and replay

| Path | Content |
|---|---|
| `rapport.html`, `resultats.png` | Full report and figures (in French) |
| `summary.csv`, `summary.json`, `comparison_128.json` | Metrics per run and paired comparisons |
| `PREPARATION_AUDIT.json` | Check of the last 64 training pulses on the 12 output lanes |
| Raw outputs (`noisy_training_130_output_native_part1.zip`, `_part2.zip`, 41 MB) | Main results, controls and all training checkpoints: assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-exploratory/releases/tag/exploratory-data-1); unzip both here |
| `oracle_128/`, `oracle_python_complete/`, `pilot_not_counted/` | Python reference runs used as oracles (not counted as seeds) |

With Python 3, NumPy, SciPy, Matplotlib and g++ (C++17), from this folder:

```sh
unzip noisy_training_130_output_native_part1.zip && unzip noisy_training_130_output_native_part2.zip   # from the release
python3 build_kernel.py
python3 build_native.py
python3 native_run.py --workers 8   # reuses existing results; move output_native/ away to recompute
python3 control.py
python3 validate.py
python3 validate_native.py
python3 report.py
```
