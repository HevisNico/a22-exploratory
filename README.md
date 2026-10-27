# Exploratory simulations (not certified)

These studies test the A22 physical kernel with a point simulator, outside the certified setting:
noise, other inputs, other topologies, ablations of the learning rule and longer training. They are
sampled simulations, without the certified engine; each finding holds for its stated protocol and
sample.

The model, the certified results and their proofs are in the main repository,
[HevisNico/a22-interval-replay](https://github.com/HevisNico/a22-interval-replay). These studies were
moved here from its `exploratory/` folder; earlier raw-data downloads are listed in this repository's release
[`exploratory-data-1`](https://github.com/HevisNico/a22-exploratory/releases/tag/exploratory-data-1).

## Current interpretation

**The learned network has no demonstrated advantage over the predefined static directional
control on the completed probe18 challenge. Physical input blocking has a separate, conditional
benefit in a cell/short-chain recovery challenge; no transmission advantage of perfect blocking
was detected in the author's reported spaced-input network campaign.**

These are different questions. The **learning guard** controls gain updates during protection.
**Physical input blocking** controls admission of input current during FAST/SLOW.
Turning off the learning guard with learning frozen does not remove physical protection.

See [Follow-up results and evidence status](FOLLOWUP_RESULTS.md) for the protocols, numbers,
limits and outstanding publication work. The follow-up archives described there have not yet
been published in this repository. The first three follow-up studies were supplied as archives
and reviewed with AI assistance; the 540-evaluation network campaign is currently an
author-reported summary only. These labels must remain visible until public artifacts are linked.

| Question | Current finding | Scope |
|---|---|---|
| Does learning beat a simple static directional control? | Static: 594/594 complete words; learned: 498/594. On reserved test noise: 198/198 versus 176/198. | Repeated perturbations within six existing learned devices; reserved noise, not new held-out devices. |
| Which parameter changes explain the difference? | Replacing only interior gains gives 54/54 complete words instead of 40/54. Replacing only b by 1.1 leaves 40/54 words and reduces mean test work by 6.82%. | Matched factorial interventions at fixed states and inputs; no new learning. |
| Can physical input blocking help? | Yes, in the local after-signal challenge: it prevents residual input from delaying recovery enough to lose the next signal. | Fixed-gain cells and four-cell chains; a parasite arriving first can still occupy recovery. |
| Is perfect blocking needed at the tested spaced-input regime? | No advantage detected: all six rho values, including 1, pass the reported 540 evaluations. | Author-reported result: 30 independent realizations, parasite amplitude 0.4, source gaps 20–24; very sparse FAST exposure. |

The static control sets gains to (3,3,3) in layers 1–6 and (1,3,1) in layers 7–130,
with b = 1.1 everywhere. It uses no learned entrance. It was prescribed before the new
outcomes; it is not a claim of optimality over all possible static or learned designs.

## What the earlier studies still establish

- **Self-organization under their protocols.** Learning finds transmitting configurations from a
  nominal low-gain state that does not ignite without adaptation. Noisy training outperforms
  clean training of the same duration in the studied settings
  ([training-noise study](gate_noise_130/README.md)).
- **Gain allocation matters.** Learned mean gains near 1.5 work below the smallest successful
  uniform gains of the tested grid, and shuffling learned gains destroys transmission
  ([gain sweep](gain_sweep_shuffle_130/README.md)). This does not establish superiority over a
  designed non-uniform allocation or an energy advantage.
- **The learning guard limits gain growth.** Removing it allows saturation; restoring it stops
  further growth in the tested conditions ([guard intervention](gate_cap_restore_130/README.md)).
  Those interventions retain physical refractory protection.
- **Selectivity depends on the comparator.** The learned network rejects many lateral probes
  relayed by uniform gain 4. A simple rule already matched the learned interior in the earlier
  [selectivity study](selectivity_130/README.md); the follow-up static control also supplies a
  working entrance and outperforms learning on its bounded challenge.
- **Modeled work depends on the protocol.** Earlier savings against a saturated network with
  parasites do not imply savings against the stronger directional control. In the follow-up,
  static mean work is about 7.11% lower without probes and 7.13% lower with the paired probes.
  These are evaluation-time model integrals, not acquisition or lifecycle costs and not
  measured hardware energy ([energy study](energy_130/README.md)).
- **Sampled uncertainty and noise can coexist with successful baseline transmission.** The
  [six-device pilot](joint_uncertainty_noise_130/README.md) remains evidence for that limited
  statement; it is not a parameter-box guarantee or a guarantee against parasites.

The negative comparisons limit claims of functional superiority. They do not invalidate the
separate, conditional mathematical results in the
[main repository](https://github.com/HevisNico/a22-interval-replay).
Timing under the noisy exploratory protocols is approximate, not a new proof of exact timing.

## Earlier published studies

| Folder | Question | Key result |
|---|---|---|
| [`robustness/`](robustness/README.md) | How does the kernel react to noise, closer pulses, other shapes and topologies? (18 and 130 layers, 128 training pulses) | Gradual degradation for small noise; discrete losses for larger noise; losses accumulate with depth. Works with gaps down to 7 and with all tested topologies without noise. |
| [`ablations_130/`](ablations_130/README.md) | Which part of the learning rule matters? (130 layers, 128 training pulses, 20 seeds) | Without learning from that nominal low-gain initialization, the network never ignites. With only 128 training pulses, plasticity left active during protection gave no complete word even without noise, and with noise the training does not reach layer 130. |
| [`noisy_training_130/`](noisy_training_130/README.md) | Does longer noisy training install a robust regime at 130 layers? (20 seeds, paired controls) | Yes in 20/20 seeds, against 0/20 for clean training of the same duration. Its 24-pulse test partly reused training noise (see the correction in its README). |
| [`gate_noise_130/`](gate_noise_130/README.md) | Is the learning guard needed for robustness? Does the effect hold at three noise levels? (2,048 training pulses, 20 seeds per level) | The learning guard is not needed for transmission in that protocol; without it gains saturate. Physical protection remains. The noisy-training benefit is confirmed at all three levels with fully separate noise. |
| [`gate_cap_restore_130/`](gate_cap_restore_130/README.md) | Does the gate stop gain growth, or only the cap? (caps 4, 8, 16; gate restored after one pulse; 20 seeds per level) | Without the gate, gains follow the cap; with it, they stay near 1.5 whatever the cap; restoring it stops growth at once. |
| [`fixed_gain_130/`](fixed_gain_130/README.md) | Can high gains fixed by hand replace learning? (gains 4 from t = 0; two input rates; 20 seeds per level) | Yes: 60 of 60 complete words, with better timing; at a faster rate, fast recovery is also needed. |
| [`gain_sweep_shuffle_130/`](gain_sweep_shuffle_130/README.md) | How large must uniform gains be? Does the placement of learned gains matter? (uniform sweep 0.3 to 4; three shuffle types; 20 seeds per level) | Uniform gains need 1.8 / 2 / 3; learned gains work at about 1.5; shuffling them destroys transmission. |
| [`energy_130/`](energy_130/README.md) | Is the gated network cheaper to run? (energy reserve integrated; matched gate on/off from the same state; 20 seeds per level) | No: it costs 2 to 11 % more, mostly through a longer slow protected phase. |
| [`selectivity_130/`](selectivity_130/README.md) | Does the learned structure reject spurious inputs? (6 frozen configurations, 7 probe scenarios, 20 seeds per level) | It rejects 90 to 96 % of lateral probes that saturated networks relay; a simple rule matches it after the learned entrance. |
| [`joint_uncertainty_noise_130/`](joint_uncertainty_noise_130/README.md) | Can fixed per-port parameter uncertainty and link noise coexist during learning and test? (130 layers, 6 paired seeds, ±1e-4) | All six uncertain/noisy baseline words complete; 3/6 with lateral decoys. Exploratory sampling only. |

## What remains open

- Whether learning offers an advantage under a separately specified task requiring adaptation.
  The completed static-control comparison does not establish such an advantage.
- Whether learning beats a non-uniform static control under an explicitly matched gain budget;
  the completed follow-up did not hold that budget fixed. Mean gain alone is not a cost law.
- Whether direction can be learned from isotropic initial gains. A simple static entrance
  already works in the follow-up challenge; its mere existence is no longer an open question.
- A practical benefit of physical input blocking under a stated input distribution and operating
  regime. Neither the local grid nor the reported spaced-input campaign establishes a global
  advantage or coverage of all phases, amplitudes and rare events.
- Learning convergence under bounded noise, broader physical and initial-state uncertainty,
  and transfer to other topologies. Finite point samples do not cover every realization.

The completed follow-ups have stopped. No parameter search, new training or higher-rate
campaign follows automatically from these results. The immediate work is to publish the
missing evidence and make the current claims reproducible; see the
[publication checklist](FOLLOWUP_RESULTS.md#publication-checklist).

The code, runs and reports were produced with AI assistants under the author's direction.
AI-assisted review and numerical replay are not independent expert review.
Earlier reports retain their original protocols and results; their conclusions should be read
with the follow-up qualifications above.
