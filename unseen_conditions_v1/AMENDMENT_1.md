# Amendment 1 — validation fixture for chronological continuation

Recorded prospectively, before any new numerical calculation. It changes one validation fixture
and adds the schedule that fixture needs. Protocol, cohorts, conditions, candidates, selection
rule, scoring, inference and every design or test job are unchanged.

## The failure

Validation attempt 1 (source lock `fbfbf418…`) is published unchanged in
`validation_failures/attempt1_fbfbf418/`; its report `VALIDATION.json` has SHA-256
`cecb05e623926408e7771444cbe6617262c44f8195cb337a5ca65d2ee3fdcbbd`.

- H = 1 parity with the untouched kernel passed (outputs, work and states bitwise identical).
- The continuation fixture failed: 64 training pulses, checkpoint, then 64 more pulses from
  t = 512, compared with one continuous 128-pulse run. The driver stopped with
  `layer=45 lane=1 nonchronological continuation`.

## Cause

At the split the training waves are still in flight. In the 64-pulse checkpoint the cells of
layer 45 have local times up to 533.5 (cell (45, 1)), later than the arrival of the next pulse
there. Near the learning front successive waves overlap, so a continuous 8-spaced stream cannot be
cut at t = 512 and resumed. The driver's chronology guard refused, as designed. The fixture tested
a case the study never uses: in the study every resumption follows a 512-unit quiet interval.

## Change

- `driver.cpp`: a third source schedule, `trainquiet`, identical to `train` (spacing 8) except a
  512-unit interval between pulses n/2 − 1 and n/2. Schedules `train` and `test`, used by every
  design and test job, give the same dates as before.
- `validation.py`: the continuation fixture now splits only at a quiet point, as the study does:
  `prefix_64` (64 training pulses), then `suffix_64` from the checkpoint at t = 8·63 + 512 with
  labels from 64, compared with `quiet_128`, one continuous run of the same 128 pulses with the
  same quiet interval. Same noise stage and keys (`train`) for the three runs; the comparison
  criteria (identical labels, timing within 1e-7, learned parameters within 1e-7) are unchanged.
- `SOURCE_SHA256.txt` updated for the two files.

Known limitation: link noise of an event with a mixed-origin (negative) label is keyed by its
ordinal in the parent row, which differs between the continuous and the resumed run. If such an
event occurs after the split, the fixture can fail for that reason alone; the failure would be
recorded and reviewed, not bypassed.

## Procedure

The implementation is rebuilt in a fresh copy (new source lock). `registration.json` then records
this amendment (`previous_failure_sha256`, `replacement_source_lock_sha256`,
`public_prospective_record_url`), as `validation.py` requires before a retry, and the attempt-1
report is placed back in `validation/` so that the launcher enforces it.
