# validation/

Audit records of the gate-noise study: pilots, solver comparisons, the original bisection outputs
(`bisection_original/`), the noise audit and the I/O repairs.

`uniform_normal_0_1.states`, `uniform_ungated_0_0.states` and `uniform_ungated_0_2.states` are
working copies written by `unify_solver.py`, which moves each finished pair to `output/`. They are
complete: their SHA-256 equal those of the trained states `normal_0_1.states`, `ungated_0_0.states`
and `ungated_0_2.states` cited by this study and by the other 130-layer experiments. The matching
`uniform_*.json` files had been copied while still being written and were truncated; they were
removed in v4.4. No script or result used them.
