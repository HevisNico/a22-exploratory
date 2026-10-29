# Implementation notes — code prepared, numerical validation not run

The protocol is the exact corrected text at repository revision
65e51bfb9988ef5cb95c42fcb8b8ac2152054822. Preparation of these source files does
not complete its registration gate. No source in this directory was uploaded to
GitHub as part of code preparation.

## Numerical changes relative to the published kernel

The four original files in reference_vendor are copied from
joint_uncertainty_noise_130/src at commit
211584f0355903f952d410165aa455c2b27390ba. vendor retains the same equations, with
these explicit changes in work_cell.cpp only:

1. Add a three-port ACTUATION vector H, set per physical cell by the driver.
2. Multiply the READY main-admission current by H on each port. All static and
   adaptive modes go through the same function and read the same H files.
3. Include H in the maximum effective gain used by the conservative continuous
   resource bound. The modeled main-admission work uses the same modified current.
4. Resume the cell clock from initial->time. Checkpoints retain q,z,b and time;
   their READY phase and cleared auxiliaries are required. During the quiet
   interval, the original READY charge equation advances q without a manual reset.

No change is made to the plasticity rule, auxiliary timing equations, control-gain
caps, recovery cap, input noise distribution or resource/overlap guards.

## Domain clarification requiring implementation review before registration

Static setpoints are initialized at min(template gain, actual per-port C cap).
In particular, uniform_4 must respect caps slightly below four under the base
C uncertainty, just as learned control gains must. H then multiplies this
control gain for every arm. This initialization detail must be explicitly
reviewed with the registered implementation; it is not silently added to the
published protocol text. There are no numerical results motivating it.

## Scoring, costs and shortcuts

Word scoring is implemented independently in C++ and Python. Every expected
label must occur once, in order, on every output lane. Negative/foreign labels
are assigned to a word by the protocol's fixed time-boundary rule; events are
never dropped. Reversals across a word boundary invalidate both affected words.
Timing RMS is reported separately and uses only valid adjacent-label pairs.
No absolute output-latency cutoff is introduced.

The oracle intentionally sees all four test words of every static candidate.
Its score is not used to choose the primary global static. Rested static
evaluation is a computational shortcut for the post-change epoch; exact rest
equivalence must pass on all twelve templates before the shortcut is enabled.
The chosen robust/oracle statics' pre-change work is then actually simulated.
If that prehistory is numerically unassessed, the corresponding deployment is
also unassessed; its work is not treated as zero.

In families 1–3 the acquired arms process 2,048 extra acquisition pulses before
512 service pulses, while statics can start immediate service. This is the
protocol's lifecycle-overhead comparison, not equal calibration exposure. In
the drift family every selected arm includes its pre-change lifetime. Tables
separate acquisition/prehistory from service work. Summed work over all four
scenarios is not one continuous physical device lifetime.

## Refusals and execution faults

Driver exit code 10 identifies the existing admitted-domain/resource guards
(including auxiliary regeneration, raw/error overlap and root bracketing).
These cases are numerically unassessed, not proven physical failures. They
remain unsuccessful in operational word counts and have full zero-to-one
success bounds in the sensitivity analysis.

Input corruption, chronology/frozen/cap violations, output capacity/step limits,
timeouts and integrity failures stop the campaign and forbid inference. Failed
or partial outputs are retained for review; there is no seed replacement or
automatic retry after a fault. The 12-hour clock starts at design execution
and continues through the pause for committing design selection and the test
phase. Analysis itself can be run later on a complete saved campaign.

## Evidence gate limits

The launcher checks evidence fields, hashes and consistency. It does not contact
GitHub, OSF or Zenodo, authenticate a receipt or prove that a reviewer entered
truthful evidence. Actual server records and protection settings require review.
Do not fill the example with invented links or set flags merely to open a gate.
There is no force/unregistered mode in the launcher. Low-level C++ executables,
like any editable source, are not an access-control boundary; use the launcher.

## Validation still pending

The gated validation suite will compare the H=1 kernel with the untouched
reference, verify checkpoint continuation and frozen invariants, test H's
effect on isolated charge/work and central-link removal, verify arm pairing,
and check the static rest shortcut on every candidate. A tolerance of 1e-7 model
units/parameter units is used for split-continuation comparisons; H=1 parity
and static-rest shortcut comparisons require exact output and work equality.
Dedicated validation seed 930901 is outside both cohorts. A failure is retained
and requires a public prospective amendment before a new implementation is tried.

Code compilation and metadata/gate tests do not validate the physical solver,
registration evidence, experiment conclusions or statistical power.
