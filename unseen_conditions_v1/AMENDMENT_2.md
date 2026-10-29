# Amendment 2 — validation tolerances for rest equivalence, non-vacuous continuation check

Recorded prospectively, before any new numerical calculation on a registered source lock. It
changes only `validation.py` (and the matching sentences of `IMPLEMENTATION_NOTES.md`). Protocol,
cohorts, conditions, candidates, selection rule, scoring, inference, `driver.cpp` and every design
or test job are unchanged. Amendment 1 is kept.

## The failure

Validation attempt 2 (source lock `2575b7aa…`) is published unchanged in
`validation_failures/attempt2_2575b7aa/`; its report `VALIDATION.json` has SHA-256
`face9d14a40195da726ba3bce727f7ecb6a2e59310bf67f9cf98ee366e952f9e`.

- H = 1 parity with the untouched kernel passed.
- The continuation fixture (Amendment 1) passed.
- The static rest-shortcut fixture failed on the first candidate:
  `Rested static shortcut is not exact: static_00`.

## Cause

`validation.py` required the fresh run (candidate at rest from t = 768) and the continued run
(32 pulses, 512-unit quiet interval, then frozen from the checkpoint) to have bitwise-identical
outputs and work. In the retained outputs the two runs agree on everything that the study scores:
same 384 output events with the same labels on all 12 lanes, same words, same final events, same
fires and per-layer event counts, identical terminal states. They differ only by binary64
roundoff: output times by at most 1.1e-13 model units, work components by a relative 6e-16. The
two runs start from different time origins, so the same arithmetic is done on different floating
values; bitwise equality was an unattainable criterion, not a property of the model. The protocol
asks to "verify this rest equivalence", not for bitwise equality; the word "exact" came from
`IMPLEMENTATION_NOTES.md`.

## A second defect found in the same review

The continuation fixture compared output events, but during the 128 training pulses the waves die
out before the output layer (layer counts reach 0 around layer 100 of 130). That comparison had
0 events and was vacuous; only its parameter check (four learned fields) was informative. The same
holds for the output part of the H = 1 parity check, which is also checked on work and states.

## Change (`validation.py` only)

- **Rest equivalence**, for each of the 12 candidates: word outcomes and counts identical
  (`words`, `complete_words`, `missing_labels`, `duplicate_labels`, `ambiguous_events`,
  `outside_labels`, `order_violations`, `final_events`, `interval_pairs`, `fires`,
  `layer_event_counts`, `input_pulses`); identical output labels and output times within 1e-7
  model units (the tolerance already used for split continuation); each work component within a
  relative 1e-9; static parameters bitwise unchanged; the fixture must have output events. The
  report records the maximum differences and whether outputs happen to be bitwise identical.
- **Continuation**: in addition to the existing checks, the per-layer event counts and fires of
  `prefix_64` + `suffix_64` must equal those of `quiet_128` exactly, work must add up within a
  relative 1e-9, and all seven state fields of every cell (not only four) must agree within 1e-7.
- **H = 1 parity**: also requires identical per-layer event counts and fires; the report records
  the number of output events.

## Pre-check of the amended suite

To avoid a third failure caused by the fixtures themselves, the complete amended suite was run once
in a throwaway copy (unregistered build, placeholder registration, dedicated seed 930901 only, no
design or test device): status PASS in 13 s. Continuation: 51 899 events after the split, counts
additive, relative work difference 5.6e-15, state difference 0.0. Rest equivalence, 12 candidates:
384 output events each, maximum time difference 5.7e-13, maximum relative work difference 3.7e-15.
Acquired-frozen, isolated charge/work/cut self-test and arm pairing: PASS. This pre-check is not
the registered validation; the registered run on the new source lock is still required and its
result will be published whatever it is.

## Procedure

As for Amendment 1: rebuild in a fresh copy (new source lock); `registration.json` records this
amendment with an entry for each earlier failure (`cecb05e6…` and `face9d14…`) pointing to the new
source lock, as `validation.py` requires; both earlier reports are placed back in `validation/`.
