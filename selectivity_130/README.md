# Directional selectivity: what does the learned gain structure buy? (exploratory)

**Status: exploratory point simulations, not certified.** 2,562 tests: 6 frozen configurations × 7 input
scenarios × (3 noise levels × 20 seeds + 1 noise-free case). Protocol and primary endpoints fixed in
advance (`PROTOCOL.json`). Full report: `report.html` (English).

## Question

With the protection gate, the learned gains stay moderate: most lateral ports are below the gain at
which a single pulse can fire a cell at rest (g ≈ 1.61), while most central ports are above it. Without
the gate, every gain saturates at 4. Does the learned configuration **reject spurious inputs** that a
saturated network relays, while still transmitting the true signal?

## Configurations (gains and b frozen in all tests)

| Configuration | Gains | b |
|---|---|---|
| Learned | Normally trained (with gate) | Learned |
| Ungated trained | Trained without gate (saturated) | Its own learned b |
| Uniform 4 | 4 on every port | Same as learned, cell by cell |
| Uniform 2 | 2 on every port | Same as learned |
| Median rule everywhere | Central 2.187, lateral 0.996 on every cell | Same as learned |
| Median rule after layer 6 | Learned layers 1–6; median rule in layers 7–130 | Same as learned |

The median values were fixed from the 60 noisy training checkpoints before any probe result was seen.

**Scenarios.** True source pulses interleaved with 24 probes per trial: an isolated lateral pulse at 100 %
or 50 % amplitude, a central pulse at 50 %, a pulse injected on the wrong source lane, background noise
with the true signal, and noise only. **Primary endpoints:** fraction of probe identities reaching layer
130 (including mixed contamination), and strict recall of the true pulses.

## Results

**Isolated full-amplitude lateral probes**, fraction reaching layer 130 (low / medium / high noise):

| Configuration | Probe reach | Strict true recall |
|---|---|---|
| Learned | 9.8 / 4.4 / 6.0 % | 99.32 / 99.88 / 99.86 % |
| Ungated trained, uniform 4 | 100 % | about 100 % |
| Median rule after layer 6 | 0 % | 100 % |

- **Against saturation**, the learned network rejects about 90 to 96 % of lateral probes (paired
  intervals well below zero), at a small cost in true recall (0.1 to 0.7 points).
- **Uniform 2** also rejects weakened probes (lateral or central at 50 %), sometimes slightly better than
  the learned network, but relays full-amplitude lateral probes far more (learned is 85 to 94 points
  lower).
- **The median rule everywhere fails to broadcast**: with weak laterals in the first layers, the
  single-lane source never reaches all 12 output lanes (true recall 91 to 99 points lower).
- **The median rule after layer 6 matches or beats the learned network on most probe types**: zero
  isolated lateral probes reach the output, with full true recall. With background noise, the trade-off
  depends on the measure: the learned network recovers slightly more true pulses (+0.7 to +1 point at low
  and medium noise) but produces more separate false emissions (about 12 to 14 per trial, against none).
- **Energy:** with full-amplitude lateral probes, the learned network does 12.9 to 14.0 % less modeled
  work than uniform 4 with the same b, because rejected probes are not processed downstream. In clean
  tests it does slightly more work (see [`../energy_130/`](../energy_130/README.md)).

## Reading

- **The learned configuration is selective, unlike a saturated network.** This is a functional benefit
  of keeping gains below saturation, and it can also save energy when spurious inputs are present.
- **A simple rule does as well in the interior** (central about 2.2, lateral about 1.0), once the
  entrance is taken from the learned network. Fine-grained learned gains are therefore not necessary
  for selectivity in layers 7 to 130. Together with the shuffle study (random rearrangements of the
  learned interior fail), this suggests that the interior needs a consistent central/lateral
  calibration rather than a specific learned pattern.
- **The entrance is where the learned gains matter most**: a homogeneous rule cannot spread a
  single-lane source to all 12 lanes.
- **Directional bias was present before learning**: the initial gains (0.3, 1.2, 0.3) already favour the
  central port. This study shows adaptation and calibration of a biased architecture, not discovery of
  direction from an isotropic start.

## Validation and audit

`AUDIT.json`: 2,562 datasets, all raw outputs recounted, 30,640 injection timings checked (0
violations), 0 unattributed events, energy residual below 4.1e-13; 183 clean historical regressions
matched. The reserve stays above 57.8 (continuous bound). Provenance tracks the raw pulses active at each
firing, not the exact counterfactual contribution of residual charge.

## Files and replay

| Path | Content |
|---|---|
| `report.html`, `FINDINGS.txt`, `probe_reach.png`, `true_recall.png`, `pure_false_reach.png` | Report, findings and figures |
| `summary.json`, `metrics.csv` | Means, paired bootstrap intervals, layer profiles; per-seed metrics |
| `PROTOCOL.json`, `CALIBRATION.json`, `MANIFEST_SHA256.json`, `ENVIRONMENT.json` | Protocol, frozen median values, checksums |
| `VALIDATION.json`, `AUDIT.json` | Local checks, regressions and audit |
| `src/`, `reference/` | Kernel with provenance instrumentation; pinned model reference and licenses |
| Raw data (`selectivity_130_results.zip`, `selectivity_130_inputs.zip`, 40 MB) | Assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-exploratory/releases/tag/exploratory-data-1); unzip here |

With Linux, g++, Python 3, NumPy and Matplotlib, from this folder:

```sh
g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
g++ -O3 -std=c++17 -ffp-contract=off src/unit.cpp -o validation/unit
python3 validate.py
python3 run.py          # reuses matching results; move results/ away to recompute
OPENBLAS_NUM_THREADS=1 python3 analyze.py
OPENBLAS_NUM_THREADS=1 python3 report.py
```
