# Energy cost of the protection gate (exploratory)

**Status: exploratory point simulations, not certified.** 427 datasets: 130 layers, 12 lanes, 20 seeds
per noise level plus one deterministic noise-free case. Full report: `report.html` (English).

## Question

With the protection gate, the learned gains stay moderate (about 1.5); without it, they saturate at 4.
Is the gated network cheaper to run, in the model's own energy law?

## Energy law (unchanged from the model)

dE/dt = 10(100 − E) − W, where W sums, with unit coefficients: admitted main current, main fast drain, a
constant power of 1.1 during the slow protected phase, admitted auxiliary current, the three auxiliary
drains, and actual gain and b movement. Values are model work units, not joules. **A static gain has no
maintenance cost in this law.** No cost term was changed for this study.

## Protocol

- **Direct intervention (primary).** Both branches load exactly the same normally trained checkpoint
  (same gains, b, relaxed q, E = 100) and can learn during a 128-pulse held-out test; the only difference
  is that the gate-off branch may increase gains during protection. 61 pairs, verified by checkpoint hash.
- **Acquisition plus test.** Both rules are rerun from the same nominal state on 2,048 noisy training
  pulses, then each network receives the same 128-pulse test. All learned checkpoints were regenerated.
- **Frozen comparison (secondary).** Learned gains and b frozen, against uniform gain 4 with the same b.

## Results

**Direct intervention: work of gate-on minus gate-off** (paired 95 % interval):

| Noise | Work difference | Complete words, on / off | Recall, on / off |
|---|---|---|---|
| Low | +6.8 % [+5.6, +8.0] | 18/20, 17/20 | 99.49 %, 99.98 % |
| Medium | +3.8 % [+3.3, +4.2] | 19/20, 20/20 | 99.997 %, 100 % |
| High | +1.8 % [+1.7, +1.9] | 20/20, 20/20 | 100 %, 100 % |

**Acquisition plus test**, total work of gate-on minus gate-off: +11.0 % (low noise), +6.4 % (medium),
+3.1 % (high); −2.3 % in the single noise-free case.

**Frozen comparison**: the learned network costs +0.4 to +0.9 % more than uniform gain 4.

**Where the difference comes from** (direct intervention, matched test): about 90 % of the extra cost
is the **slow protected phase**, whose constant power of 1.1 lasts longer in the gated networks because
they end with a lower recovery rate b (mean 0.88 / 0.97 / 1.03 against 1.08 without the gate). About
10 % is extra admitted main current. The gate saves the cost of gain movement (about 5,300 to 5,400 units
per test), which is small in comparison.

## Reading

- **The gated rule is not cheaper in this model; it costs slightly more** (2 to 11 %).
- The reason is mostly indirect: networks with saturated gains also learn a faster recovery, which
  shortens the costly slow phase. Gain size itself is nearly free here, because the law charges nothing
  for maintaining a gain, and stronger inputs close admission earlier.
- An energy advantage for moderate gains therefore cannot be claimed within the model's cost law. A
  cost of maintaining large gains would be a separate hypothesis, to be justified and fixed in advance.
- The reserve never approaches depletion (smallest continuous lower bound 57.4; smallest sampled value
  96.5), so energy does not limit the dynamics in these runs.

## Validation and audit

An independent Python oracle reconstructs q, m, z, b, E, every work term and the pump input from raw
inputs on 25 local cases, with its own threshold events: maximum differences 3.2e-13 (work component),
1.6e-9 (reserve), 1.6e-13 (event times). Pump input is integrated from its rate 10(100 − E) rather than
from the balance identity (largest network residual 8.4e-7). `AUDIT.json`: 427 datasets, 61 matched
pairs, 0 errors. Optional regression against earlier outputs: 366 comparisons, 0 differences beyond
tolerance. `CORRECTIONS.patch` lists the changes from the earlier energy experiment.

## Files and replay

| Path | Content |
|---|---|
| `report.html`, `paired_energy_comparisons.png`, `gain_motion_and_saturation.png` | Report and figures |
| `summary.json`, `metrics.csv` | Paired bootstrap summaries and work components; per-run metrics |
| `PROTOCOL.json`, `MANIFEST_SHA256.json`, `ENVIRONMENT.json` | Protocol, checksums, environment |
| `VALIDATION.json`, `validation/`, `validate_independent.py` | Independent oracle and its results |
| `AUDIT.json`, `REGRESSION.json` | Campaign audit and optional regression |
| `src/`, `reference/` | C++ solver with energy budget; pinned model reference and licenses |
| Raw data (`energy_130_training.zip`, `energy_130_results.zip`, 54 MB) | Assets of the [`exploratory-data-1` release](https://github.com/HevisNico/a22-interval-replay/releases/tag/exploratory-data-1); unzip here |

With Linux, g++, Python 3, NumPy, SciPy and Matplotlib, from this folder:

```sh
g++ -O3 -std=c++17 -ffp-contract=off src/fixture_bridge.cpp -o validation/fixture_bridge
g++ -O3 -std=c++17 -ffp-contract=off src/experiment.cpp -o experiment
python3 validate_independent.py
python3 run.py          # reuses matching outputs; move training/ and results/ away to recompute
python3 analyze.py
python3 report.py
```
