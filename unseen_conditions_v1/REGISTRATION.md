# Registration record — preregistration v1

Evidence for the registration and launch gate of [`PROTOCOL.md`](PROTOCOL.md). Every value
below was read from the GitHub API after the events it records.

| Item | Value |
|---|---|
| Protocol file | `unseen_conditions_v1/PROTOCOL.md` |
| Merged by | [pull request #3](https://github.com/HevisNico/a22-exploratory/pull/3) |
| Merge commit | `42cfd3111bc79f38d722a27f635d40d1167658a9` (parents `211584f`, `65e51bf`) |
| Merge time recorded by GitHub | 2026-10-29 00:54:53 UTC |
| SHA-256 of `PROTOCOL.md` at the merge commit | `6e87280e8ceef910f2d38c09ee599f900fd0a8a2db65594a4945a720415db867` |
| Tag | `prereg-unseen-conditions-v1` → commit `42cfd3111bc79f38d722a27f635d40d1167658a9` |
| Release | [prereg-unseen-conditions-v1](https://github.com/HevisNico/a22-exploratory/releases/tag/prereg-unseen-conditions-v1), published 2026-10-29 00:59:28 UTC |

## Protection rules in force

| Ruleset | Target | Rules | Bypass |
|---|---|---|---|
| `protect main` (active) | default branch | no deletion, no force push, pull request required | none |
| `protect prereg tag` (active) | `refs/tags/prereg-*` | no deletion, no update, no force push | none |

This repository has no CI, so no status check is required. A merged pull request and a
protected tag make later changes visible; they are not an independent third-party
timestamp.

## External timestamp

None recorded yet. If a published deposit (for example Zenodo or OSF) is made, add its
public URL, its service-recorded publication time and its DOI here through a pull request.

## Implementation clarification, recorded before any calculation

The implementation initializes every static setpoint at `min(template gain, the port's physical
cap C)` (`driver.cpp`, `log(min(g, cap))`). Because C varies by ±1e-4 around 4, `uniform_4` is
slightly below 4 on some ports. Learned gains are bounded by the same cap, and H then multiplies the
control gain in every arm. The protocol text does not state this initialization; it is recorded
here, with no numerical result available, as part of the implementation to be registered.

## Implementation

| Item | Value |
|---|---|
| Implementation merged by | [pull request #5](https://github.com/HevisNico/a22-exploratory/pull/5), merge commit `a357841900516968745bc5ec77aa234c1b16a529` |
| Source hashes | `SOURCE_SHA256.txt` (24 files) |
| Build, from that commit, no simulation run | `SOURCE_LOCK.json`, SHA-256 `fbfbf4183737bb82a4277b7cdbb260f5b8ccc4caaf182c46e366e2bf9b7e80bf`; binaries `driver` `0c2009bf…`, `driver_reference` `e57efa8f…`; g++ 13.3.0, Python 3.12.14, NumPy 2.3.5; logs in `build_evidence/` |
| Registration evidence read by the launcher | `registration.json` |

The launch gate is complete once this record is merged. Validation, design and test follow the
protocol's order; the design selection must be committed before any held-out device is generated.

## Amendment 1 (validation fixture)

Validation attempt 1 failed on the continuation fixture; its record is published unchanged and the
correction is described in [`AMENDMENT_1.md`](AMENDMENT_1.md). Recorded before validation is retried:

| Item | Value |
|---|---|
| Failure record | [pull request #7](https://github.com/HevisNico/a22-exploratory/pull/7); attempt-1 report SHA-256 `cecb05e623926408e7771444cbe6617262c44f8195cb337a5ca65d2ee3fdcbbd` |
| Amendment merged by | [pull request #8](https://github.com/HevisNico/a22-exploratory/pull/8), merge commit `7bd4cb6446f1829ebcd0b766ade6b2e1f3fcad63` |
| Rebuild from that commit, no simulation run | `SOURCE_LOCK.json`, SHA-256 `2575b7aa8a76ca4c72f7d06a1f6c47b7e024ca07530a86ea057b06f76b3f87de`; binaries `driver` `60f2a7d6…`, `driver_reference` `67aff94f…`; logs in `build_evidence/amendment1/` |
| `registration.json` | implementation and lock updated; amendment entry added |

## Amendment 2 (validation criteria)

Validation attempt 2 failed on the static rest-shortcut fixture (bitwise equality, unattainable under
binary64 roundoff); its record is published unchanged and the correction is described in
[`AMENDMENT_2.md`](AMENDMENT_2.md). Recorded before validation is retried:

| Item | Value |
|---|---|
| Failure record | [pull request #10](https://github.com/HevisNico/a22-exploratory/pull/10); attempt-2 report SHA-256 `face9d14a40195da726ba3bce727f7ecb6a2e59310bf67f9cf98ee366e952f9e` |
| Amendment merged by | [pull request #11](https://github.com/HevisNico/a22-exploratory/pull/11), merge commit `2c483817dcc751f0ee477db8b84d26de56071b6f` |
| Rebuild from that commit, no simulation run | `SOURCE_LOCK.json`, SHA-256 `c041e033e4e81ba589d6d02c490823aa5319cb9b66e1524c737e3b4820af705c`; binaries `driver` `60f2a7d6…`, `driver_reference` `67aff94f…` (identical to the previous build: `driver.cpp` unchanged); logs in `build_evidence/amendment2/` |
| `registration.json` | implementation and lock updated; one amendment entry for each earlier failure (`face9d14…`, `cecb05e6…`), both pointing to the new lock |
