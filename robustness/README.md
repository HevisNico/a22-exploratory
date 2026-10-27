# Robustness of the A22 kernel outside the certified setting (exploratory)

**Status: exploratory point simulations, not certified.** No result in this folder is a proof. The
certified engine is not used. Each number below comes from a finite set of sampled runs (2 to 6 seeds
per condition) of one point simulator, and holds for these protocols only.

The question: the certified results assume an ideal model (no noise, exact pulse shape, exact reset,
fixed protocol, one topology). How does the same physical kernel behave when these idealizations
are relaxed?

## Protocol

Every run starts from the nominal gains (q = 0.1, b = 0.08) and simulates the full training (128 pulses
at times 8k). It then sends 24 test pulses from time 4096, with intervals that repeat the pattern
1, 1.1, 1.05, 1.2, 1, 1.15 times a minimum gap (20 unless stated). The source is lane 0 only. No
learned gain is substituted: every state comes from the simulated training.

Measures, at the last layer unless stated:

- **Pulses recovered**: fraction of (reference lane, source pulse) pairs that produce exactly one
  emission. The reference is the same topology, without noise.
- **Complete words**: fraction of reference lanes that recover all 24 pulses exactly once, with no
  extra emission (this says nothing about the accuracy of the dates).
- **Relative RMS interval error**: RMS of (output interval − source interval) / source interval, over
  consecutive recovered pairs only. Read it together with the losses.

Noise models (all impulsive, not continuous white noise):

- **Transmitted charge**: each pulse on each connection is multiplied by exp(σZ − σ²/2), Z standard
  normal (mean charge preserved, coefficient of variation ≈ σ).
- **Jitter**: centred uniform delay of the stated standard deviation, independent per connection and
  pulse, on top of a fixed delay of 0.1 (also present in the reference).
- **Charge q**: centred uniform jump at each arrival in READY mode, standard deviation 0.9 σ_q.

Unless stated, noise is applied to the test pulses only, after a noise-free training. In the
`allnoise` series it is present during the whole training as well.

## Main observations (18 layers)

| Condition | Pulses recovered | Complete words | Relative RMS error |
|---|---:|---:|---:|
| Charge noise σ = 0.001 / 0.01 | 100 % / 100 % | 100 % / 100 % | 0.012 % / 0.118 % |
| Charge noise σ = 0.03 | 98.8 % | 70.8 % | 0.52 % |
| Charge noise σ = 0.1 / 0.2 | 87.7 % / 73.6 % | 0 % / 0 % | 1.40 % / 1.60 % |
| Jitter 0.001 / 0.01 / 0.05 | 100 % | 100 % | 0.011 % / 0.11 % / 0.57 % |
| Charge q noise 0.001 / 0.03 | 100 % / 98.1 % | 100 % / 61.1 % | 0.017 % / 0.73 % |
| Charge + jitter 0.01 / 0.03 / 0.1 | 100 % / 97.4 % / 86.8 % | 100 % / 37.5 % / 0 % | 0.12 % / 0.62 % / 1.53 % |
| **Noise during training too**, 0.01 / 0.03 / 0.1 | **100 %** | **100 %** | 0.13 % / 0.44 % / 0.66 % |

- **Small noise degrades the dates gradually.** Below σ ≈ 0.01, all pulses are recovered and the
  interval error grows roughly in proportion to the noise.
- **Larger noise causes discrete losses**: when a threshold crossing changes, a pulse can disappear.
  Fidelity then breaks in jumps, not smoothly.
- **Training under noise gave a more robust learned state** in these samples: with noise present
  from the start, all pulses were recovered up to σ = 0.1, and no gain moved during the test pulses,
  whereas noise applied only after a noise-free training made some gains move again (8 to 26 moves
  per run at σ = 0.1). This is consistent with a learning rule that keeps increasing a gain until the
  cell responds before its delayed error signal, here for the noisy inputs actually seen. Three seeds
  per level do not establish a general adaptation mechanism.

## Inputs, shapes and depth

- **Closer pulses (no noise)**: all 24 pulses are recovered down to a minimum gap of 7 (the training
  period is 8; the certified theorem requires 20). At 6, 80.9 % are recovered; below, losses grow
  quickly (17 % at 1.5).
- **Pulse shapes**: source decay constants ×0.9 to ×1.1, fixed or alternating from pulse to pulse, at
  constant integral charge: all pulses recovered, about 0.19 % RMS error in the alternating case.
- **130 layers**: without noise, exact transmission. With charge noise σ = 0.01 (2 runs), all pulses
  recovered (about 0.24 % RMS). With σ = 0.1 (2 runs), no test pulse reaches the output; the first
  silent layers are 103 and 100. **Losses accumulate with depth**: what is tolerable at 18 layers
  may not be at 130.

## Topologies (no noise, then σ = 0.03)

Rings of 12, 24 and 48 lanes; 3, 5 or 7 parents per cell; random feedforward graphs with 3 or 5
parents (3 graphs per degree). Without noise, every tested topology transmits complete words on all
reachable lanes. With σ = 0.03, robustness varies with the graph and with the gain normalization
(between about 90 % and 100 % of pulses recovered). The `added` variants, which increase the total
initial gain, were at least as robust as the variants at constant total gain (100 % against 94–95 % with
5 parents). No recurrent connection and no
layer skipping were tested.

## What is not tested here

- **Ablations of the mechanism** and **longer noisy training** are in separate studies:
  [`../ablations_130/`](../ablations_130/README.md) and [`../noisy_training_130/`](../noisy_training_130/README.md).
- Continuous (white) noise on the charges, which would need another integrator.
- The resource variable E is not integrated (as in the kit); the analytic barrier E in [50, 100] is used.

## Validation

- The original simulator reproduces the 21,302 historical events of the first 18 layers (maximum date
  error 1.6e-11); the extended simulator reproduces them too (2.7e-11).
- 27 first threshold crossings (3, 5 and 7 parents, three decay constants, three widths) are checked
  against SciPy `solve_ivp` (maximum error 3.4e-15). This local check does not validate every
  hybrid path of the campaign.

## Files and replay

| Path | Content |
|---|---|
| `A22_point_simulator_kit/` | The original point simulator, its regression reference and result |
| `experiment/rapport.html`, `experiment/resultats.png` | Full report and figures (in French) |
| `experiment/summary.csv`, `summary.json` | Metrics for every run |
| Raw outputs (`robustness_output.zip`, 10 MB) | Emissions and states of every run: asset of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-exploratory/releases/tag/exploratory-data-1); unzip into `experiment/` |
| `experiment/extended_simulate.py`, `extension.diff` | Extended simulator and its changes to the original |
| `experiment/cases.json`, `selected_cases.json` | Run definitions |
| `experiment/PROVENANCE.json`, `VALIDATION.json` | Script hashes and validation results |

From `experiment/`, with Python 3 (standard library for the simulations; NumPy, SciPy and Matplotlib
for validation and report):

```sh
unzip robustness_output.zip   # downloaded from the exploratory-data-1 release
python3 build_extension.py
python3 run_selected.py      # reuses existing results; move output/ away to recompute
python3 validate.py
python3 make_report.py
```

The code, runs and report were produced with AI assistants under the author's direction.
