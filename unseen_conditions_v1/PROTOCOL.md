# A22 adaptation to held-out operating conditions — preregistration v1

Status: protocol registered before any simulation or candidate evaluation for
this study. The first public GitHub commit containing this file is the
registration timestamp. The implementation and its hashes must also be committed
before numerical validation and before design/test simulations. This study is
separate from the earlier six-device and TouchReal experiments.

## Question and permitted conclusion

Does the unchanged local A22 plasticity rule improve complete-word transmission
on new devices under held-out operating conditions, relative to one robust static
configuration selected in advance on separate design devices?

The designer knows the four shift families below, but not held-out physical
draws, noise, source lanes or cut locations. This tests transfer to new conditions
within the stated challenge, including a larger gain-variation range; it cannot
establish robustness to arbitrary unknown kinds of change.

The static search is finite. "Best static" means best among the 12 candidates
listed below, not the optimum over every possible per-cell static assignment.
The hindsight oracle is an optimistic envelope of this same family on this
finite test, not a theoretical upper bound on all learning algorithms.

## Devices, source and noise

* Network: 130 layers, 12 periodic lanes, three incoming ports. All 12 final
  lanes are scored. One source pulse train; canonical pulse shapes unchanged.
* Independent design devices: integer physical seeds 910100 through 910107 (8).
* Independent held-out devices: physical seeds 920100 through 920131 (32).
  None is an earlier learned device. Conditions/repetitions share a device and
  are not additional independent replicates.
* The base C, Lm, Ls, Le, M fields are independently uniform within ±1e-4 of
  nominal per cell and port. Larger heterogeneity below concerns effective main
  actuation gains, not auxiliary timing constants.
* Link amplitude: independent mean-one lognormal noise, log standard deviation
  0.10. Link delay 0.1 plus centered uniform jitter of standard deviation 0.03.
  No additive background or spurious source events.
* Calibration and evaluation use distinct SHA-256 namespaces. Every comparison
  on a device/condition uses the same source dates and counter-based latent
  evaluation noise keys. Divergent traffic can request different keys; matching
  latent fields does not force identical realized downstream pulse histories.
* Fixed namespace: `a22-unseen-conditions-v1`. Seeds for each purpose are
  SHA256 of namespace, group, device, condition and stage, first 12 hex digits
  modulo 1,000,000,000. Other draws use a documented counter-based generator;
  Python hash() and nondeterministic RNGs are prohibited.

## Four equally weighted condition families

1. **Source shift.** Design source lanes cycle through 0,2,4,6,8,10; held-out
   lanes cycle through 1,3,5,7,9,11. No cut and no large actuation variation.
   The published static template is lane-equivariant: this shift alone is not
   expected to defeat a valid directional design.
2. **Broken link.** Source lane 0. Remove the central incoming link (port 1)
   of one cell. Design cut layers cycle through 24,48,72,96; held-out layers
   through 36,60,84,108. The receiver lane is drawn uniformly per device.
   Removal means no current or auxiliary event from that link, not attenuation
   to an invalid zero-amplitude pulse. Other paths remain. No dead endpoint is
   removed from the score. Reachability of all outputs must be checked without
   inspecting transmission outcomes.
3. **Gain heterogeneity.** Source lane 0, no cut. Effective main actuation gain
   is `exp(z[p])*H[cell,port]`. Independent H is uniform on [0.9,1.1] for design
   devices and [0.8,1.2] for held-out devices. H is fixed during acquisition and
   evaluation. The plasticity equation, z cap and auxiliary equations are
   unchanged. Main-admission work and the conservative resource bound must
   include H. No claim is made about independently varying all auxiliary
   constants by ±20%, which can violate this simulator's admitted pulse domain.
4. **Post-acquisition drift.** Source lane 0, no cut. Acquire with H=1. After
   2,048 pulses and the declared quiet interval, replace H by a new independent
   [0.9,1.1] design or [0.8,1.2] held-out draw. Keep learned z,b unchanged and
   leave learning active from the very first post-change test pulse. There is
   no unscored post-drift retraining period. This is an abrupt gain change after
   a quiet interval, not drift during FAST/SLOW or a continuously varying
   auxiliary constant.

## Acquisition and evaluation schedule

* Learning always starts from the original z=log(0.3,1.2,0.3), b=0.08, q=r,
  READY state. Its rule is used as published; no per-condition tuning.
* Acquisition: exactly 2,048 pulses at source spacing 8. In families 1–3,
  acquire in the eventual operating condition. In family 4, acquire before the
  gain change. No favorable stopping or extra training.
* The first evaluation source date is 512 model units after the last acquisition
  source date. Every checkpoint must be READY with cleared auxiliaries before
  that date. Propagate q analytically through the quiet interval; never reset
  z or b. If the stated interval is insufficient, stop for a documented software
  review rather than lengthening it after seeing scores.
* Evaluation: one continuous 512-pulse stream, split into four consecutive
  128-label words. Source gaps repeat 20,22,21,24,20,23. No state resets between
  words. At design selection use the first 256 labels (two words), with design
  noise only. Test uses all four words and new reserved noise.
* The first post-drift word is scored. Later words measure adaptation within
  the same predeclared stream; none can be discarded.

## Comparators and static search

**Learning active:** locally acquired on the device; plasticity remains active
throughout evaluation. This is the primary adaptive arm.

**Acquired then frozen:** same acquisition checkpoint, z and b frozen during
evaluation. This extra control distinguishes acquisition from online adaptation.
Its acquisition cost is included in its hypothetical deployment total.

**One robust static:** one candidate, used unchanged on every held-out device
and condition. No learned entrance is copied. Six templates, each with uniform
b=0.5 or b=1.1, produce exactly 12 candidates:

| Template | Layers 1–6 | Layers 7–130 |
|---|---|---|
| directional_1 | (3,3,3) | (1,3,1) |
| directional_1_5 | (3,3,3) | (1.5,3,1.5) |
| directional_2 | (3,3,3) | (2,3,2) |
| uniform_2 | (2,2,2) | (2,2,2) |
| uniform_3 | (3,3,3) | (3,3,3) |
| uniform_4 | (4,4,4) | (4,4,4) |

Run every candidate on all 8 design devices × 4 families × 2 words. Select
lexicographically: (1) largest minimum complete-word fraction across the four
families, (2) largest overall complete-word fraction, (3) lowest nominal sum of
gains over all ports, (4) largest b, (5) smallest candidate ID. The design set is
fixed and no candidates are added. Publish and commit DESIGN_SELECTION.json
before generating any held-out device fields or running held-out outcomes.

**Static hindsight oracle:** evaluate all 12 candidates on each held-out
device/condition, using the same four test words. Its score is the maximum word
count obtained by a single candidate over those four words, ties resolved by
the same gain/b/ID ordering. It intentionally sees the test outcomes and is
therefore only an optimistic diagnostic. Never select the global robust static
or tune the learning rule from these oracle outcomes. Do not call the oracle a
deployable test estimate or a proven upper bound.

## Outcomes and accounting

Primary word success requires every expected label exactly once, in order, on
all 12 output lanes, with no extra, out-of-word or ambiguous events. Group final
events by fixed numeric source-label blocks; ambiguous and foreign events are
assigned by time relative to source-word boundaries plus the declared quiet
propagation delay 15.6 (130×0.12). This auxiliary boundary rule cannot remove an
event from accounting. All final events must belong to exactly one block.
Report label coverage, duplicates, ambiguous events and interval RMS separately.
No absolute-latency tolerance is part of word success.

For each device and arm, average the four condition-family success fractions,
each based on four words. The paired primary difference D is active minus the
one robust static, in complete-word fraction. A device, not a lane, pulse, word
or condition, is the inferential unit.

Secondary outcome: the existing nine-component modeled work integral, including
gain and b learning, summed over the whole declared deployment history.
For learned/frozen arms this includes all acquisition plus all evaluation work.
For statics in families 1–3, no acquisition-only inputs are needed; their total
is evaluation work. For drift, the 2,048-pulse pre-change lifetime is required
for all arms, and its work is included for the chosen robust and oracle statics.
Because static parameters are fixed and the quiet interval restores the same
operating state, oracle search can evaluate rested candidates first; the chosen
candidate's pre-change work must subsequently be simulated and added. Verify
this rest equivalence before using that shortcut.

Publish acquisition and service components separately, success/cost pairs,
per-device work differences and ratios, and the declared horizon (2,048+512
learning pulses, 512 immediate static service pulses except drift). Do not
infer lower energy for equal delivered service when success differs. These are
model work integrals, not measured hardware energy. Offline design-search,
oracle-search and software compute costs are reported as excluded; oracle cost
is an optimistic diagnostic, not a fair deployable energy claim.

Simulator refusals are retained as unsuccessful expected words for the primary
operational score, and separately counted as numerically unassessed, not proven
physical transmission failures. If any arm refuses on a paired case, include a
sensitivity interval assigning that unassessed outcome all possible successes
from zero to four. No functional superiority claim is allowed unless its
direction survives those bounds. Unavailable work is never imputed as zero.

## Fixed inference and decision rule

* 32 paired device-level primary differences. No optional sample-size increase.
* Exact one-sided sign test on nonzero D: H0 is that a device is no more likely
  to favor active than static, conditional on a non-tie. Alpha=0.05. Ties and
  the number of non-ties are reported. This tests win probability, not mean D.
* Paired device bootstrap: 50,000 resamples of 32 whole device blocks, fixed
  seed 934771; report the two-sided 95% percentile CI for mean D. Conditions,
  words and lanes must never be bootstrapped as independent devices.
* A positive study claim requires sign-test p<0.05, a strictly positive lower
  bootstrap limit for mean D, and refusal-sensitivity robustness above. Otherwise
  report no demonstrated adaptive advantage. A negative or null result is
  published with the same tables. Bootstrap coverage is approximate at n=32.
* Family-level and temporal-word breakdowns, frozen comparison, oracle gaps and
  work are descriptive; no additional significance claims or post-hoc subgroups.

## Execution, validation, stopping and publication

Commit this protocol first, then commit the implementation/source hashes before
any numerical fixture. Validate unchanged-case parity, frozen invariants,
H=1 equivalence, H effect on charge/work, cuts, chronological continuation and
rest equivalence on dedicated validation seeds outside both cohorts. Fixtures
cannot select new operating parameters or static candidates. If validation
fails, stop, publish the failure and a prospective amendment before rerunning;
never silently replace a failed preregistered analysis.

Then run design, commit the selected global static and all design results, and
only then generate and run held-out devices. Fixed finite jobs; four workers;
each subprocess has a 300-second timeout and the campaign a 12-hour wall-clock
limit. A limit, execution fault or failed integrity check stops inference and
produces an incomplete-study report. No seed replacement, domain-guard removal,
higher input rate, retuning, automatic extra training or favorable early stop.

Publish source, environment, exact protocol/selection commits, physical/noise
generation keys, all job statuses, raw final events, checkpoints, work components,
per-device paired scores, bootstrap/sign-test code and results. An output cap or
upload problem is reported; it cannot justify discarding unfavorable results.
Keep all simulator/auxiliary/resource guards active. Point simulations only:
no interval certificate, specialist-review claim or hardware conclusion.

Source basis: HevisNico/a22-exploratory commit
211584f0355903f952d410165aa455c2b27390ba,
joint_uncertainty_noise_130/src. Prepared with AI assistance at the author's
request. Earlier negative outcomes are not overwritten.
