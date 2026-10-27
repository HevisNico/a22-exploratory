# Uniform gain sweep and shuffled learned gains (exploratory)

> **Follow-up qualification.** A fully static non-uniform control has since been tested on the separate probe18 challenge. It outperforms the learned networks there; a comparison at an equal gain budget remains open. See [follow-up results and evidence status](../FOLLOWUP_RESULTS.md#1-static-directional-control-and-recurrence); publication of those follow-up archives is pending.

**Status: exploratory point simulations, not certified.** 1,471 network evaluations; 130 layers, 12
lanes, 128 test pulses, 20 network seeds per noise level plus one deterministic noise-free control. The
gain grid and shuffle definitions were fixed before the results (`PROTOCOL.json`). Full report:
`report.html` (English, figures embedded).

## Questions

1. How large must uniform gains, fixed before the first pulse, be to transmit the word?
2. Does the **placement** of the learned gains matter, beyond their distribution?

## Protocol

Test: 128 pulses, intervals 20 × (1, 1.1, 1.05, 1.2, 1, 1.15), noise σ = 0.05 / 0.10 / 0.15 with jitter
0.015 / 0.030 / 0.045, on a new noise field separate from all earlier training and tests.

- **Uniform sweep**: all 4,680 gains set to the same value at t = 0 (0.3 to 4) and never changed; b
  starts at 0.08 and keeps its original update. Secondary: b fixed at 1.1 or 0.08.
- **Learned reference**: the gated networks of `gate_noise_130` after 2,048 pulses, gains and b frozen.
- **Shuffles** of the learned gains, two draws per seed, each preserving the exact gain multiset of every
  layer: within each layer; within each layer and port (preserves each port's distribution); within
  layers 7 to 130 only (layers 1 to 6 untouched). b stays at its learned cell.

## Results at layer 130

**Uniform fixed gains** (complete words out of 20; recall):

| Gain | Low noise | Medium | High |
|---:|---|---|---|
| 1.2 | 0, 0 % | 0, 0 % | 0, 0.07 % |
| 1.4 | 0, 0 % | 0, 1.2 % | 0, 7.2 % |
| 1.6 | 0, 65.0 % | 0, 69.7 % | 0, 69.9 % |
| 1.8 | 20, 100 % | 10, 99.5 % | 0, 96.3 % |
| 2 | 20, 100 % | 20, 100 % | 6, 99.1 % |
| 2.5 | 20, 100 % | 20, 100 % | 19, 99.96 % |
| 3 | 20, 100 % | 20, 100 % | 20, 100 % |
| 4 | 20, 100 % | 20, 100 % | 20, 100 % |

Smallest grid value with 20/20 complete words: **1.8 (low), 2 (medium), 3 (high)**. Gains 0.3 to 0.9
give no transmission. Fixing b at 1.1 gives a similar threshold (1.6 fails; 2 passes at low and medium
noise).

**Learned gains, unchanged and shuffled** (complete words; mean recall):

| Noise | Learned, unchanged | Shuffle in layer | Shuffle in layer and port | Shuffle layers 7–130 |
|---|---|---|---|---|
| Low | 19/20, 99.45 % | 0/40, 0.02 % | 0/40, 2.4 % | 6/40, 47.2 % |
| Medium | 20/20, 100 % | 0/40, 0 % | 0/40, 2.5 % | 8/40, 90.7 % |
| High | 19/20, 99.99 % | 0/40, 1.4 % | 0/40, 9.0 % | 3/40, 89.7 % |

Mean learned gain: 1.52 (low), 1.55 (medium), 1.52 (high); 1.06 without noise.

## Reading

- **The learned networks transmit with less gain than any uniform setting that works.** With 19 or 20 of
  20 complete words, their mean gain (about 1.5) is below the smallest working uniform gain at every noise level, and half of it at high
  noise (3). Uniform gains near the learned mean (1.6) give no complete word.
- **The placement of the learned gains is essential.** Shuffling them, even while preserving each
  layer's and each port's distribution, destroys transmission. Keeping the first six layers intact
  helps but remains far below the unchanged network. This is consistent with the relational nature of
  `G_rel`: good gains are tied to the arrival phases of each cell.
- **Learning is not required** if large uniform gains can be set by hand (see
  [`../fixed_gain_130/`](../fixed_gain_130/README.md)). What the rule provides is a lane-specific
  allocation, found autonomously from the nominal state, that works at a lower gain level.

## Limits

- Mean gain is not an energy cost; the resource variable E is not integrated, and in this model E never
  limits the dynamics.
- The grid is coarse (1.6 then 1.8); thresholds are grid observations, not exact values.
- This uniform-gain/shuffle study did not test a hand-designed **non-uniform** allocation.
  A later separate probe18 study does; its favorable static-control result does not settle a
  comparison at an equal gain budget (see the follow-up qualification above).
- Shuffling gains while keeping b in place can also break gain–b associations.
- Two shuffle draws of one seed are correlated; analyses average them within seed before bootstrapping
  over the 20 seeds. 20/20 gives an exact 95 % lower bound of about 83 %.

## Validation

Audit: 1,471 files, all final outputs recounted, 366 shuffles verified (exact multiset preservation),
0 errors; gain immutability asserted in every run. Four reference comparisons give exact JSON identity with
the previous kernel. The learned inputs include the documented reconstruction of the truncated
`normal_2_9.states` (`INPUT_REPAIR.json`); no seed was dropped.

## Files and replay

| Path | Content |
|---|---|
| `report.html`, `uniform_gain_sweep.png`, `learned_gain_shuffles.png` | Report and figures |
| `summary.json`, `metrics.csv` | Groups and paired bootstrap intervals; per-realization metrics |
| `PROTOCOL.json`, `PROVENANCE.json`, `INPUT_HASHES.json`, `ENVIRONMENT.json` | Protocol and identities |
| `AUDIT.json`, `PERMUTATION_AUDIT.json`, `VALIDATION.json`, `validation/` | Audit and checks |
| `src/`, `kernel.diff` | Sources and the minimal freeze-gain change |
| Raw data (`gain_sweep_shuffle_130_results.zip`, `_inputs.zip`, `_permutations.zip`, 22 MB) | Assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-exploratory/releases/tag/exploratory-data-1); unzip here |

With Python 3, NumPy, Matplotlib and g++ C++17, from this folder:

```sh
g++ -O3 -std=c++17 -ffp-contract=off src/control.cpp -o control
python3 run.py          # reuses existing results; move results/ away to recompute
python3 analyze.py
python3 report.py
```
