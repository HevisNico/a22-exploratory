# Follow-up results and evidence status

This document updates the interpretation of the earlier exploratory studies. None of these
point experiments extends the certified theorem in
[a22-interval-replay](https://github.com/HevisNico/a22-interval-replay).

## Evidence available for this update

The first three source archives below were supplied by the author and examined with AI
assistance before this documentation update. Their raw inputs, outputs and original reports
are **not yet published in this repository or its releases**. The numerical summaries below
therefore do not substitute for public reproduction artifacts.

| Study | Source supplied by the author | Review performed | Public evidence status |
|---|---|---|---|
| Six-state recurrence, test noise and static control | `A22_probe18_six_states_noise_and_static_control_EN(1).zip` | All 3,514 manifest entries matched; protocol and reports inspected. | Archive publication pending. |
| Targeted ablation and reserved-noise stopping test | `A22_targeted_ablation_and_reserved_noise_stop_test_EN(1).zip` | All 1,862 manifest entries matched; metrics recomputed from all 828 factorial/reserved-noise probe outputs; 12 saved gate-null pairs compared. | Archive publication pending. |
| Residual coupling in cells and short chains | `A22_residual_protection_cell_and_chain_EN(1).zip` | All 5,189 manifest entries matched; 2,560 simulations replayed with matching outputs and metrics; 40 ODE-oracle fixtures rerun. | Archive publication pending. |
| Residual coupling at source gaps 20–24 | Author's completion summary; no archive supplied for this review. | Summary read only; raw results and independence of realizations not independently checked. | Protocol, implementation, raw outputs and hashes pending. |

The `(1)` suffixes identify the supplied filenames; they are not proposed scientific version
numbers. Manifest checks establish package integrity. Replays check implementation behavior.
Neither constitutes independent specialist review or a proof of model-wide robustness.
This update adds documentation only and launches no experiment.

## 1. Static directional control and recurrence

The six previously learned uncertain/noisy devices, seeds 3000–3005, are reused at 130 layers.
No new acquisition or physical-field draw is performed. The fully static control has gains
(3,3,3) in layers 1–6, then (1,3,1) in layers 7–130, with b = 1.1 everywhere. It copies no
learned entrance, gains or recovery parameters.

The completed comparison contains **594 paired physical perturbations**, not the interim
count of 552. Each pair receives the same actual probe time/amplitude within a common
admissible window, the same physical field and matched latent test-noise keys.

- Static: **594/594** complete words; learned: **498/594**.
- All no-probe contexts pass for both designs.
- Learned outcomes include 67 points with missing pure-source responses and 29 further
  points with extras but no pure-source loss. The static control has neither.
- Static mean model work is **7.1115% lower without probes** and **7.1315% lower with the
  paired probes**. These figures exclude acquisition and whole-campaign/lifecycle costs.
- State 3000 has failures across several interior timing nodes; the other five states show
  source losses only at the last sampled timing node in their coarse maps. This is not a
  claim that all unsampled times are safe.

These are repeated measurements within six devices, not 594 independent networks.
Pure-source tags omit residual-charge ancestry; missing tags do not alone prove the same
local refractory mechanism at every failing point.

## 2. Factorial attribution and reserved test noise

The targeted factorial study changes entrance gains (E), interior gains (I), and recovery b
(B) separately, with identical actual input perturbations for each matched comparison.
Eight designs, six states, three amplitudes and three timings give **432 probe evaluations**.

| Intervention from the learned state | Complete words | Change in mean model work |
|---|---|---|
| None | 40/54 | Reference |
| Only b replaced by 1.1 | 40/54 | −6.8191% |
| Only interior gains replaced by (1,3,1) | 54/54 | −0.3168% |
| Only entrance gains replaced by (3,3,3) | 38/54 | About −0.012% |

Changing only b reduces pure-source-loss points from 11 to 8 but leaves 14 extra-output
points. Changing only the interior gains removes both missing pure sources and extras on
this grid. The entrance replacement alone does not explain the selectivity advantage.

On the reserved test-noise field, the static design preserves **198/198** words versus
**176/198** for the learned networks. It weakly dominates word preservation at every pair,
strictly improves at least one point in each device, and has lower mean test work in each
device. All 12 no-probe references pass. This is **new test noise on the same six devices**,
not an independent held-out device cohort. The prescribed stopping criterion was met.

The 12 frozen gate-on/gate-off comparisons are identical as required by the implementation:
the flag controls **gain learning**, which is disabled in both arms. Physical protection
is retained. These null comparisons do not measure the guard's effect during acquisition.

Conclusion: no demonstrated learning benefit over this predefined static design for the
finite task. Interior gain allocation explains the observed selectivity correction; b
explains most of the work difference. Neither conclusion is a universal statement.

## 3. Physical residual coupling: conditional benefit

This separate experiment changes only input admission during protected phases:

```text
READY: dq/dt = K(r − q) + I(t)
FAST:  dq/dt = −Aq + rho I(t)
SLOW:  dq/dt = −bq + rho I(t)
```

rho = 0 is original physical blocking. Even rho = 1 retains the refractory phases,
threshold rules, fixed FAST duration and end reset: it does not remove all protection.
Gains and b are fixed. The end-of-FAST reset erases surplus charge accumulated in FAST;
a pulse arriving in FAST can still have a tail in SLOW.

The fixed design uses gains (1,2,2), b = 0.18 or 1.1, rho = 0, 0.1, 0.25, 0.5 or 1,
parasite amplitudes 0.5, 1 or 1.5, and one-cell/four-cell systems.
All **2,560 evaluations**, including 220 references, complete without refusal; all references pass.

In the after-signal challenge (96 perturbation cases per row), receiver-complete words are:

| Length | b | rho 0 | rho 0.1 | rho 0.25 | rho 0.5 | rho 1 |
|---|---|---|---|---|---|---|
| 1 | 0.18 | 93 | 17 | 9 | 6 | 3 |
| 4 | 0.18 | 92 | 17 | 9 | 6 | 3 |
| 1 | 1.1 | 87 | 59 | 41 | 30 | 18 |
| 4 | 1.1 | 79 | 59 | 41 | 30 | 18 |

Positive residual forcing cannot advance the downward SLOW-to-READY crossing from the
same starting episode. It can delay recovery enough to lose the next legitimate response.
This local statement does not order whole-word outcomes after histories diverge.

The original model also loses legitimate responses when a parasite triggers protection first.
No tested residual comparator demonstrates a paired before-order Pareto improvement over
rho = 0 on the missing/extras criteria. Some individual after-order cases favor residual
coupling, so this is not pointwise dominance or a comparative reversal between the two orders.

Receiver matching uses a tolerance of 0.5 against the same-rho reference; it can accept a
wrong-origin spike in the expected window. Active-input lineage omits residual-charge
ancestry. Both channels and their disagreements are retained in the source package.
These grid counts are not deployment probabilities. No energy advantage is claimed.

## 4. Spaced-input network campaign: author-reported result

**Evidence level: author-reported completion summary only.** The protocol, source code,
raw outputs and analysis for this campaign have not been examined for this update.

The author reports 30 independent realizations evaluated in 18 conditions each, for
**540/540 successful evaluations**: no missing signals, extra outputs or simulator refusals.
All six tested rho values, including 1, pass with parasite amplitude **0.4** and source
spacings **20–24** time units.

Reported maximum recovery duration changes from **1.83 to 4.48** time units; the maximum
output displacement attributable to leakage is **2.34 × 10⁻⁶** time units.
The reported arrival-phase counts are 1,391 injections in READY, 48 in SLOW and one in FAST.
The exact counting convention and per-rho/per-realization breakdown need the public archive.

The reported finding is **no detected transmission advantage of perfect isolation in this
regime**, not equivalence over all inputs, phases or amplitudes. In particular, amplitude
0.4 differs from the stronger perturbations in the earlier challenges. The 540 evaluations
are paired/repeated conditions within 30 realizations, not 540 independent devices.

The stated stopping rule was applied: no higher input rate, retuning or automatic expansion.
No energy conclusion is supplied. These observations do not reverse the local recovery
mechanism, and they do not establish that the learning rule is superior.

## Publication checklist

- [ ] Publish the three supplied archives without silently changing their original contents;
      record exact asset URLs, byte sizes and SHA-256 hashes in this repository.
- [ ] Publish the spaced-input campaign's frozen protocol, source/solver changes, environments,
      physical/noise draws, raw inputs/outputs, per-realization paired metrics and refusal accounting.
- [ ] Check its 540-case accounting, all baseline references, physical input pairing and the
      arrival-phase counting convention; retain both timing and lineage measurements.
- [ ] Supply documented build/replay commands and a manifest checker for each new archive.
      Reproduction should be explicit and should not trigger new learning or new experiments.
- [ ] Replace the provisional evidence labels above only after the corresponding artifacts
      and checks are publicly available.
- [ ] Add a short reciprocal link from the main repository to this exploratory repository.
      The main theorem's assumptions and the exploratory performance comparisons must stay distinct.

The next scientific priority is an accurate, reproducible synthesis and external review.
A new experiment requires a new question and protocol; it is not an automatic response to
an unfavorable or null result.
