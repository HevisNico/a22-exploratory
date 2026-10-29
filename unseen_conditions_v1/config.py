"""Fixed design choices. Importing this module generates no devices or results."""
from pathlib import Path
import hashlib
import math

ROOT = Path(__file__).resolve().parent
NAMESPACE = 'a22-unseen-conditions-v1'
BASE_COMMIT = '211584f0355903f952d410165aa455c2b27390ba'
PROTOCOL_REVISION = '65e51bfb9988ef5cb95c42fcb8b8ac2152054822'
DESIGN_DEVICES = tuple(range(910100, 910108))
TEST_DEVICES = tuple(range(920100, 920132))
CONDITIONS = ('source_shift', 'broken_link', 'gain_heterogeneity', 'post_acquisition_drift')
CANDIDATES = tuple(range(12))
ACQUISITION_PULSES = 2048
DESIGN_PULSES = 256
TEST_PULSES = 512
WORD_LENGTH = 128
EVAL_START = 8.0 * (ACQUISITION_PULSES - 1) + 512.0
WORK_NAMES = ('main_admission', 'main_fast', 'main_slow', 'aux_admission',
              'aux_mark', 'aux_silent', 'aux_error', 'gain_learning', 'b_learning')
STAGES = {'acquisition': 101, 'evaluation': 201}
WORKERS = 4
JOB_TIMEOUT = 300
CAMPAIGN_SECONDS = 12 * 3600
BOOTSTRAP_SEED = 934771
BOOTSTRAP_REPLICATES = 50000


def namespace(group, device, condition, stage):
    return f'{NAMESPACE}/{group}/{device}/{condition}/{stage}'


def noise_seed(group, device, condition, stage):
    return int(hashlib.sha256(namespace(group, device, condition, stage).encode()).hexdigest()[:12], 16) % 1_000_000_000


def counter_uniform(key, index):
    """Independent deterministic SHA-256 counter draws; no global RNG state."""
    digest = hashlib.sha256(f'{key}/{index}'.encode()).digest()
    return ((int.from_bytes(digest[:8], 'big') >> 11) + 0.5) * 2.0**-53


def condition_spec(group, device, condition):
    if group not in ('design', 'test', 'validation') or condition not in CONDITIONS:
        raise ValueError('Unknown group or condition')
    devices = DESIGN_DEVICES if group == 'design' else TEST_DEVICES
    index = device - devices[0] if group != 'validation' else device
    lanes = (0, 2, 4, 6, 8, 10) if group == 'design' else (1, 3, 5, 7, 9, 11)
    layers = (24, 48, 72, 96) if group == 'design' else (36, 60, 84, 108)
    cut_lane = int(12 * counter_uniform(namespace(group, device, condition, 'cut_lane'), 0))
    return dict(source_lane=lanes[index % len(lanes)] if condition == 'source_shift' else 0,
                cut_layer=layers[index % len(layers)] if condition == 'broken_link' else 0,
                cut_lane=cut_lane if condition == 'broken_link' else 0,
                gain_half_width=(0.1 if group == 'design' else 0.2)
                if condition in ('gain_heterogeneity', 'post_acquisition_drift') else 0.0)


def nominal_physics():
    a, k = math.log(4.0), 0.5
    m = .975 / (a / (a-k) * (math.exp(-k*.02) - math.exp(-a*.02)))
    return (4.0, math.log(1.25)/.02, math.log(8.0)/1.06, a/.15, m)


def nominal_gain_sum(candidate):
    template = candidate // 2
    if template < 3:
        interior = 3.0 + 2.0 * (1.0, 1.5, 2.0)[template]
        return 72 * 9.0 + (1560-72) * interior
    return 1560 * 3.0 * (2.0, 3.0, 4.0)[template-3]


def candidate_tie_key(candidate):
    return (nominal_gain_sum(candidate), -(1.1 if candidate % 2 else 0.5), candidate)


def reachable_outputs(source, cut_layer, cut_lane):
    lanes = {source}
    for layer in range(1, 131):
        lanes = {lane for lane in range(12)
                 if any((lane+p+11) % 12 in lanes
                        and not (layer == cut_layer and lane == cut_lane and p == 1)
                        for p in range(3))}
    return lanes
