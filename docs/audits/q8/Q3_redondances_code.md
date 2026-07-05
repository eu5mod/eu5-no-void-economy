# Q3 — Q8 redundancy and generated-code boundaries

## Purpose

Q8 should reduce repeated runtime work without creating parallel helper families that become harder to audit than the original implementation.

This document is the Q8-owned redundancy standard for helper extraction, generated literal goods, and duplicate guard layers.

## Current redundancy risks

| Surface | Risk | Q8 rule |
|---|---|---|
| Generated per-good helpers | Literal symbols are required by EU5, but generated all-good wrappers can accumulate guard layers. | Keep the literal generated surface, but move policy into generator/template and validators. |
| PR7.1 guarded dispatch | Outer active-good / pending-request wrapper may call helpers that still contain internal guards. | Do not split body helpers until all callers are inventoried. |
| Capacity helpers | Public helpers may be called from several surfaces. | Prefer changing the public helper contract once rather than editing each large dispatcher caller. |
| Debug/profile counters | Metrics can look like business state when scattered. | Centralize gates and keep metrics explicitly diagnostic. |
| Q8 docs vs PR126 docs | Duplicated methodology can drift. | Q8 owns new Q1–Q5 documents; PR126 documents remain inherited context. |

## Q8 helper-change standard

```txt
1. Public helpers remain safe and guarded.
2. Internal body helpers may be introduced only after caller inventory proves every caller has the required guard.
3. Generated helper changes must update generator/template and validation, not only generated output.
4. A refactor may reduce duplicate checks only if it does not create an unsafe call surface.
5. Documentation duplication is avoided by keeping Q8 standards in docs/audits/q8/Qx_*.md.
```

## Q8.0 baseline decision

Q8.0 adds no helper or generator changes.

It classifies Q8.4 / F4 as `PROBE_FIRST`: split guarded helpers from body helpers only after caller inventory.
