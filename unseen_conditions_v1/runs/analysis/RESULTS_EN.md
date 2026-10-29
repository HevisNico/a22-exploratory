# A22 held-out conditions: registered analysis

**NO_DEMONSTRATED_ADAPTIVE_ADVANTAGE**

32 independent device blocks. Fixed robust static candidate: 1.

| Arm | Complete words / 512 |
|---|---:|
| active | 488 |
| frozen | 470 |
| robust_static | 512 |
| oracle_static | 512 |

The 512 words per arm are repeated measurements within 32 devices.

## Primary paired-device inference

```json
{
  "devices": 32,
  "mean_difference": -0.046875,
  "wins": 0,
  "losses": 15,
  "ties": 17,
  "sign_test_p_one_sided": 1.0,
  "sign_test_null": "P(win | non-tie) <= 0.5",
  "bootstrap_mean_difference_ci95": [
    -0.068359375,
    -0.02734375
  ],
  "bootstrap_replicates": 50000,
  "bootstrap_seed": 934771,
  "bootstrap_unit": "whole paired device block",
  "positive_by_registered_statistics": false
}
```

Pessimistic bounds for all numerically unassessed paired outcomes are retained in SUMMARY.json.

## Four preregistered families

| Family | Active | Robust static | Frozen | Hindsight oracle |
|---|---:|---:|---:|---:|
| source_shift | 123/128 | 128/128 | 123/128 | 128/128 |
| broken_link | 125/128 | 128/128 | 123/128 | 128/128 |
| gain_heterogeneity | 122/128 | 128/128 | 123/128 | 128/128 |
| post_acquisition_drift | 118/128 | 128/128 | 101/128 | 128/128 |

Gain heterogeneity and post-acquisition drift were prespecified as the leading possible sources of an advantage. A gain limited to those families is not evidence for arbitrary unseen conditions.

The oracle intentionally uses test outcomes within the finite static family. It is an optimistic diagnostic, not a deployable estimate or theoretical bound.

Total modeled work includes acquisition for acquired arms and the pre-change lifetime for chosen drift statics. Static arms need no acquisition-only inputs in the other scenarios. This is the registered deployment comparison, not equal calibration exposure, measured hardware energy or a claim of equal delivered service.

All static candidates, statuses, raw files and checkpoints remain available. Passive labels do not describe every residual-charge ancestor. No interval certification or independent expert review is claimed.
