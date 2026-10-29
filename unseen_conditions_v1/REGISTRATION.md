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

## Remaining gate before any calculation

Item 4 of the launch gate: the implementation sources and their SHA-256 hashes
(`SOURCE_SHA256.txt`) are published in this folder by pull request. Still required before any
numerical validation, candidate evaluation or study simulation:

1. the merge commit of that pull request, recorded here;
2. the `SOURCE_LOCK.json` produced by `python study.py build` on the machine that will run the
   study (it adds the compiled binaries and the compiler), published here by pull request, with its
   SHA-256, since `registration.json` must cite it;
3. `registration.json` filled from these public records.
