# Fixed maximum gains: can high gains replace learning? (exploratory)

**Status: exploratory point simulations, not certified.** 130 layers, 12 lanes, 20 paired seeds,
three noise levels. Protocol fixed before the new network outcomes (`PROTOCOL.json`). The full report
is `A22_fixed_gain_controls_report.pdf` (English).

## Question

Without the protection gate, learning drives gains to their cap and transmission stays reliable
([`../gate_noise_130/`](../gate_noise_130/README.md)). Can the same reliability be obtained by choosing
high gains in advance, with no learning at all?

## Controls

All use 2,048 conditioning pulses (intervals of 8) and the same tests as `gate_noise_130`. No gain or
recovery value was chosen from held-out results.

| Control | Definition |
|---|---|
| Fixed, b = 0.08 | All gains 4 and b = 0.08 (nominal) from time zero, fixed throughout |
| Fixed, b = 1.1 | All gains 4 and b = 1.1 (its upper bound) from time zero, fixed throughout |
| Fixed gains, learned b | All gains 4 from time zero; b keeps its original local update |
| References | The learned networks of `gate_noise_130` (with and without the gate), frozen at test |

Primary test: 128 held-out pulses, intervals 20 to 24. Secondary test, declared in advance: a faster
rate, intervals 8 to 9.6.

## Results at layer 130 (20 seeds; recall, complete words on all 12 lanes)

**Original test (intervals 20 to 24):**

| Noise σ | Learned rule (frozen) | Fixed, b = 0.08 | Fixed, b = 1.1 | Fixed gains, learned b |
|---|---|---|---|---|
| 0.05 | 99.49 %, 17/20 | 100 %, 20/20 | 100 %, 20/20 | 100 %, 20/20 |
| 0.10 | 100 %, 20/20 | 100 %, 20/20 | 100 %, 20/20 | 100 %, 20/20 |
| 0.15 | 99.99 %, 19/20 | 100 %, 20/20 | 100 %, 20/20 | 100 %, 20/20 |

Relative RMS interval error: learned 0.51 / 0.84 / 1.25 %; fixed gains 0.22 / 0.45 / 0.72 %.

**Faster test (intervals 8 to 9.6):**

| Noise σ | Learned rule | Fixed, b = 0.08 | Fixed, b = 1.1 | Fixed gains, learned b |
|---|---|---|---|---|
| 0.05 | 99.38 %, 18/20 | 50 %, 0/20 | 100 %, 20/20 | 100 %, 20/20 |
| 0.10 | 100 %, 20/20 | 50 %, 0/20 | 100 %, 20/20 | 100 %, 20/20 |
| 0.15 | 100 %, 19/20 | 50 %, 0/20 | 100 %, 20/20 | 100 %, 20/20 |

With b = 0.08, the protected phase lasts 1 + ln(2.5)/b ≈ 12.45 time units, too long for intervals of 8;
with b = 1.1 it lasts about 1.83.

**Learned state** (mean gain; mean b; fraction of gains at the cap):

| Condition | Mean gain | Mean b | At cap |
|---|---|---|---|
| Learned rule | 1.52 / 1.55 / 1.52 | 0.88 / 0.97 / 1.02 | 2.4 / 1.2 / 0.4 % |
| Learned without gate | 3.92 | 1.08 | 97.7 % |
| Fixed controls | 4 | 0.08, 1.1 or learned | 100 % |

## Reading

- **Learning is not necessary for this transmission task when high gains can be set by hand.** Gains
  fixed at 4 from the start transmit every pulse in all 60 realizations, with better timing than the
  learned networks. At a faster input rate, fast recovery (high b) is also needed.
- What remains for the learning rule is to reach a working regime **from the nominal initial state**,
  with moderate gains and an adapted b. Whether that is more economical than uniform gains is tested in
  [`../gain_sweep_shuffle_130/`](../gain_sweep_shuffle_130/README.md).
- Energy and hardware cost are not measured (the resource variable E is not integrated).

## Validation

18 local solver comparisons, no label mismatch (maximum event-time difference 3.6e-13); exact network
regression from a previous learned checkpoint; independent 130-layer Python propagation of a fixed
control (all discrete scores agree, maximum time difference 1.1e-13). `AUDIT.json`: 480 new and 120
reference datasets, 1,920 test instances, final outputs recounted, fixed parameters unchanged.

The reference checkpoint `normal_2_9.states` was truncated (1,548 of 1,560 rows) and was rebuilt from the
complete JSON states; the original is kept in `validation/original_checkpoint_serialization/` and the
affected secondary test was rerun (`validation/REFERENCE_CHECKPOINT_AUDIT.json`).

## Files and replay

| Path | Content |
|---|---|
| `A22_fixed_gain_controls_report.pdf`, `fixed_gain_results.png` | Report and figure |
| `summary.json`, `results.csv`, `training.csv` | Group estimates and paired comparisons; endpoints and diagnostics per seed |
| `PROTOCOL.json`, `PROVENANCE.json`, `ENVIRONMENT.json` | Protocol, SHA-256 identities, environment |
| `VALIDATION.json`, `AUDIT.json`, `validation/` | Solver checks and audit |
| `*.diff` | Source changes relative to the previous point simulator |
| Raw outputs (`fixed_gain_130_output.zip`, 26 MB) | Asset of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1); unzip here |
| `reference_campaign/output/` | The `gate_noise_130` raw outputs (same release, `gate_noise_130_output_part1.zip` and `_part2.zip`, unzipped into `reference_campaign/`) |

With Python 3 and g++ C++17, from this folder:

```sh
python3 build.py
python3 validate.py
python3 run_campaign.py --workers 8   # reuses existing results; move output/ away to recompute
python3 analyze.py
python3 report.py
```
