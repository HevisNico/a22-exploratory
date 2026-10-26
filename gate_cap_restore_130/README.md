# Does the protection gate stop gain growth before the cap? (exploratory)

**Status: exploratory point simulations, not certified.** 427 continuations from 61 learned states;
130 layers, 12 lanes; 20 seeds per noise level and one deterministic noise-free control. The protocol
was fixed after a single pilot run (seed 0, medium noise, ungated, cap 16) and before the campaign
(`PROTOCOL.json`); it is not a preregistered study.

## Question

In [`../gate_noise_130/`](../gate_noise_130/README.md), the network without the protection gate stayed
reliable but drove almost every gain to the cap of 4. Two explanations were possible: the gate really
stops gain growth, or growth only stops because of the cap. This study separates them by raising the
cap.

## Protocol

Every branch starts from the same learned states (normal rule, 2,048 noisy training pulses, from
`gate_noise_130`; no seed excluded). Six branches cross the gate (on / removed) with the gain cap
(4, 8, 16). A seventh branch, **restored**, follows the ungated cap-16 branch for exactly one pulse,
then restores the gate. All branches from the same state share the same continuation noise.

Continuation: four independent noise blocks of 1, 127, 128 and 256 pulses (512 in total), with gains and
b kept between blocks and a silence of 3,080 time units before each block. Noise levels as in
`gate_noise_130` (σ = 0.05 / 0.10 / 0.15, jitter 0.015 / 0.030 / 0.045), with new key spaces separate from
training and earlier tests. The only physical parameter changed is the gain cap.

Primary measures: summed log-gain increments, fraction of gains at the cap, and increments requested
before the gate and the cap are applied. Secondary: complete words at layer 130 in the final 256-pulse
block.

## Results (mean over seeds; final 256-pulse block)

| Noise | Cap | Rule | Mean gain | Gains at cap | Seeds still growing | Complete words |
|---|---:|---|---:|---:|---:|---:|
| None | 4 / 8 / 16 | Gated | 1.06 / 1.07 / 1.07 | 0.09 % | 0 / 1 | 1 / 1 |
| None | 4 / 8 / 16 | Ungated | 3.92 / 7.83 / 15.64 | 97.7 % | 0 / 1 | 1 / 1 |
| None | 16 | Restored | 1.93 | 0 % | 0 / 1 | 1 / 1 |
| Low | 4 / 8 / 16 | Gated | 1.52 / 1.55 / 1.63 | 2.4 / 0.4 / 0.5 % | 16 / 18 / 18 of 20 | 18 / 16 / 12 of 20 |
| Low | 4 / 8 / 16 | Ungated | 3.92 / 7.83 / 15.64 | 97.7 % | 0 of 20 | 20 of 20 |
| Low | 16 | Restored | 2.76 | 0 % | 2 of 20 | 20 of 20 |
| Medium | 4 / 8 / 16 | Gated | 1.55 / 1.56 / 1.58 | 1.3 / 0.1 / 0.1 % | 19 / 20 / 20 of 20 | 20 / 18 / 18 of 20 |
| Medium | 4 / 8 / 16 | Ungated | 3.92 / 7.83 / 15.64 | 97.7 % | 0 of 20 | 20 of 20 |
| Medium | 16 | Restored | 2.82 | 0 % | 1 of 20 | 20 of 20 |
| High | 4 / 8 / 16 | Gated | 1.52 / 1.53 / 1.53 | 0.5 / 0.05 / 0.03 % | 20 of 20 | 19 of 20 |
| High | 4 / 8 / 16 | Ungated | 3.92 / 7.83 / 15.64 | 97.7 % | 0 of 20 | 20 of 20 |
| High | 16 | Restored | 2.76 | 0 % | 0 of 20 | 20 of 20 |

"Seeds still growing": at least one gain increased during the final block. For ungated branches,
growth has stopped only because the gains are at the cap: the requested increments stay large.

## Reading

- **Without the gate, only the cap stops growth.** Gains follow whatever cap is set (4, 8 or 16), and
  97.7 % of them end at it. Each full delayed error under protection requests an increment of 0.6 in log
  gain, so growth continues as long as inputs arrive.
- **With the gate, gains stay near 1.5 whatever the cap.** The gate limits growth by itself, independently
  of the cap.
- **Restoring the gate stops growth immediately.** After one ungated pulse, gains jump (mean about 2.8),
  then stay almost flat once the gate is back. This is causal evidence that the gate is what stops the
  growth.
- **Without noise, learning stops completely with the gate.** Under noise it is strongly reduced but not
  zero: small increases remain in most seeds over 512 pulses. No permanent stop is claimed, since the
  amplitude noise is unbounded.
- **The gate is still not needed for transmission.** Ungated networks transmit complete words in every
  case, through saturated gains. With the gate, some losses remain, and raising the cap reduced complete
  words at low noise (18 → 12 of 20). The restored branch, with moderate gains (about 2.8), transmitted
  complete words in every case.

In short: the gate is a causal stop for learning, which keeps gains moderate; robustness of transmission
does not require it in this protocol.

## Validation and audit

- **Repaired input.** The supplied checkpoint `normal_2_9.states` was truncated after 1,547 complete rows.
  It was rebuilt from the 1,560 complete states in `normal_2_9.json`; all values still present matched
  exactly (`INPUT_REPAIR.json`, `INPUT_HASHES_ORIGINAL.json`). The seed was kept in every branch.
- At cap 4, the modified kernel reproduces exactly the events and all layer metrics of the archived
  128-pulse tests (two seeds, medium noise); original and instrumented kernels agree exactly on events,
  gains and b for both rules (`VALIDATION.json`).
- `AUDIT.json`: 427 completed files, the 61 restored branches identical to the ungated branch for the
  first pulse, requested increments recounted independently as 0.6 per received pulse, 0 errors.
- `LOCAL_ANALYTIC_CHECK.json`: on one cell, a full error under protection requests 0.6 in log gain, which
  the gate blocks and the ungated rule applies.

## Files and replay

| Path | Content |
|---|---|
| `rapport.html`, `gains.png` | Full report (in French) and mean gain over the continuation |
| `summary.json`, `metrics.csv` | Groups and paired bootstrap intervals; metrics per seed, branch and block |
| `PROTOCOL.json`, `PROVENANCE.json`, `ENVIRONMENT.json` | Protocol, SHA-256 identities, environment |
| `src/`, `reference_src/`, `kernel.diff` | Modified kernel and the original sources |
| Raw data (`gate_cap_restore_130_results.zip`, `gate_cap_restore_130_inputs.zip`, 8 MB) | Profiles of the 130 layers per run, and the learned input states: assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1); unzip both here |

With g++ C++17, Python 3, NumPy and Matplotlib, from this folder:

```sh
unzip gate_cap_restore_130_results.zip && unzip gate_cap_restore_130_inputs.zip   # from the release
g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
python3 validate.py
python3 run.py          # reuses existing results; move results/ away to recompute
python3 analyze.py
python3 report.py
```
