"""Device-level inference only; never treats words, conditions or lanes as devices."""
import math
import numpy as np
import config as c


def paired_inference(differences):
    d = np.asarray(differences, dtype=float)
    if d.shape != (32,) or not np.all(np.isfinite(d)):
        raise ValueError('Exactly 32 finite device differences are required')
    wins, losses, ties = int(np.sum(d > 0)), int(np.sum(d < 0)), int(np.sum(d == 0))
    n = wins + losses
    p = sum(math.comb(n, k) for k in range(wins, n+1)) / 2**n if n else 1.0
    rng = np.random.default_rng(c.BOOTSTRAP_SEED)
    samples = d[rng.integers(0, 32, size=(c.BOOTSTRAP_REPLICATES, 32))].mean(axis=1)
    lo, hi = np.quantile(samples, [.025, .975], method='linear')
    return dict(devices=32, mean_difference=float(d.mean()), wins=wins, losses=losses, ties=ties,
                sign_test_p_one_sided=float(p), sign_test_null='P(win | non-tie) <= 0.5',
                bootstrap_mean_difference_ci95=[float(lo), float(hi)],
                bootstrap_replicates=c.BOOTSTRAP_REPLICATES, bootstrap_seed=c.BOOTSTRAP_SEED,
                bootstrap_unit='whole paired device block',
                positive_by_registered_statistics=bool(p < .05 and lo > 0))


def work_summary(device_pairs):
    """Descriptive cost only; no claim of equal delivered service or hardware energy."""
    valid = [(a, b) for a, b in device_pairs if a is not None and b is not None]
    return dict(expected_devices=32, evaluable_device_pairs=len(valid),
                mean_active_total_work=float(np.mean([a for a, _ in valid])) if valid else None,
                mean_static_total_work=float(np.mean([b for _, b in valid])) if valid else None,
                mean_paired_work_difference=float(np.mean([a-b for a, b in valid])) if valid else None,
                mean_paired_work_ratio=float(np.mean([a/b for a, b in valid if b > 0]))
                if valid and all(b > 0 for _, b in valid) else None,
                includes_acquisition=True, excluded='offline design/oracle search and software compute',
                interpretation='Modeled work over the declared deployment horizon; success may differ.')
