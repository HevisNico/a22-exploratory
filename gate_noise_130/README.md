# Protection gate × noise level at 130 layers (exploratory)

**Status: exploratory point simulations, not certified.** 20 paired seeds per condition, three noise
levels, protocol fixed before the results (`PROTOCOL.json`).

## Question

In A22, a gain can only increase while the principal cell is READY: plasticity is switched off during
protection. Is this gate what makes noisy training produce a robust network?

## Protocol

Ring of 12 lanes, 3 parents (j−1, j, j+1), 130 layers, source on lane 0 only. Initial gains (0.3, 1.2,
0.3), b = 0.08. **Every condition receives 2,048 training pulses** spaced by 8, with no seed selection.

| Noise level | Amplitude σ (log-normal, mean 1) | Jitter (std, uniform) |
|---|---:|---:|
| Low | 0.05 | 0.015 |
| Medium | 0.10 | 0.030 |
| High | 0.15 | 0.045 |

Jitter is added to a nominal delay of 0.1. Noise is drawn from a deterministic field indexed by seed,
layer, lane, port, phase, label and occurrence; **training and test use separate keys**. Compared
conditions share the same standardized noise.

Conditions: the A22 rule (**gated**), the same rule with only the READY gate on gain increases removed
(**ungated**; recovery b, delayed errors, thresholds, topology and caps unchanged), and a **clean**
control trained without noise for 2,048 pulses then tested under the same noise. Each learned state is
tested with learning active and with gains and b frozen, on independent 24- and 128-pulse words
(intervals 20 to 24). Primary criterion: 128-pulse test, learning active, layer 130.

## Results at layer 130 (128-pulse test, 20 seeds)

**Gated against ungated** (learning active):

| Noise | Gated: recall / complete words | Ungated: recall / complete words | Paired difference, 95 % CI |
|---|---|---|---|
| Low | 99.49 % / 17 of 20 | 100.00 % / 20 of 20 | −0.51 points [−1.37, 0.00] |
| Medium | 100.00 % / 20 of 20 | 100.00 % / 20 of 20 | 0.00 [0.00, 0.00] |
| High | 99.99 % / 19 of 20 | 100.00 % / 20 of 20 | −0.01 points [−0.03, 0.00] |

Sign tests with Holm correction: p = 0.75, 1, 1. Relative RMS interval error among recovered pairs:
gated 0.51 / 0.84 / 1.25 %; ungated 0.22 / 0.45 / 0.72 %.

**Noisy against clean training** (gated rule; recall, complete words):

| Noise | Noisy, active | Clean, active | Noisy, frozen | Clean, frozen | Noisy − clean, frozen, 95 % CI |
|---|---|---|---|---|---|
| Low | 99.49 %, 17/20 | 98.22 %, 0/20 | 99.49 %, 17/20 | 78.57 %, 0/20 | +20.9 points [19.2, 22.7] |
| Medium | 100.00 %, 20/20 | 95.24 %, 0/20 | 100.00 %, 20/20 | 32.45 %, 0/20 | +67.6 points [65.9, 69.1] |
| High | 99.99 %, 19/20 | 92.29 %, 0/20 | 99.99 %, 19/20 | 8.91 %, 0/20 | +91.1 points [90.2, 92.0] |

**Transfer** (frozen, recall; rows = training level, columns = test level):

| Trained at \ tested at | Low | Medium | High |
|---|---:|---:|---:|
| Low | 99.49 % | 95.15 % | 78.59 % |
| Medium | 100.00 % | 100.00 % | 99.59 % |
| High | 100.00 % | 100.00 % | 99.99 % |

**Learned state** (mean over seeds):

| Rule | Mean gain | Ports at the gain cap (4) |
|---|---:|---:|
| Gated | 1.52 to 1.55 | 0.4 to 2.4 % |
| Ungated | 3.92 | 97.7 % |

## Reading

- **The gate is not needed for robustness to noise in this protocol.** Without it, transmission is as
  good or slightly better, with better timing. The earlier hypothesis that robustness comes from the
  protection gate is not supported.
- **Without the gate, almost every gain saturates at its cap.** Robustness then comes from maximal
  gains. With the gate, gains stay moderate (about 1.5) and still give reliable transmission. The gate
  therefore keeps the learned gains far from saturation; whether this has a benefit (resource use,
  remaining plasticity, sensitivity) is not tested here.
- **Noise exposure during training is what matters, and it is confirmed.** With gains frozen at test,
  noisy training beats clean training by 21 to 91 points, more so at higher noise. This replicates the
  earlier result with fully separate training and test noise.
- **The learned margin scales with the training noise.** Training at a higher level also covers lower
  levels; training at the low level does not cover the high level.
- **Learning does not fully stop under noise** with the gate: gains still increase during the last 128
  training pulses. Since the amplitude noise is log-normal and unbounded, no permanent stop is claimed.

## Validation

Twelve local checks pass for both rules, with and without freezing. The 130-layer network at 512 pulses
matches the Python solver (maximum log-gain difference 1.5e-6); the ungated control at 128 pulses also
passes. In the 2,048-pulse root-solver audit, discrete scores and output labels are identical, but the
strict 1e-5 threshold on continuous states fails (maximum state-time difference 5.4e-4, b difference
5.1e-4); the relative RMS at test differs by less than 1.2e-8. `AUDIT.json`: frozen tests change no gain
or b, and final outputs are recounted independently. Point simulator only; no certified engine.

## Files and replay

| Path | Content |
|---|---|
| `rapport_A22_coupure_bruit.pdf` | Four-page report (in French) |
| `resultats.png`, `mecanisme.png` | Transmission at 130 layers; learned gains and saturation |
| `summary.json`, `summary.csv` | Groups, confidence intervals, paired comparisons; all layer-130 results |
| `training.csv`, `profiles.csv` | Preparation, gains, caps and late updates per seed; profiles by layer |
| `PROTOCOL.json`, `PROVENANCE.json`, `ENVIRONMENT.json` | Protocol fixed in advance, SHA-256 identities, environment |
| `AUDIT.json`, `VALIDATION.json`, `validation/` | Integrity audit and solver checks |
| Raw outputs (`gate_noise_130_output_part1.zip`, `_part2.zip`, 23 MB) | Learned states and test results: assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1); unzip both here |

**Repaired checkpoint.** In the original archive, the learned-state file `output/normal_2_9.states` was
truncated after 1,547 of its 1,560 rows. The analysis and the audit read only the JSON outputs, which are
complete, so the results reported here are not affected. The released raw outputs contain the file rebuilt from the complete
states stored in `normal_2_9.json`; all values still present in the truncated file match exactly (see
`../gate_cap_restore_130/INPUT_REPAIR.json`).

With Python 3 (see `requirements.txt`) and g++ C++17, from this folder:

```sh
unzip gate_noise_130_output_part1.zip && unzip gate_noise_130_output_part2.zip   # from the release
python3 build.py
python3 run_campaign.py --workers 8   # reuses existing results; move output/ away to recompute
python3 audit.py
python3 analyze.py
python3 report.py
```
