# US-17 — Modifier refresh lifecycle

## Objective

Ensure the persisted US-17 country baselines and corrections introduced by PR #204 are recalculated when their source state changes outside the normal monthly fallback.

## Lifecycle contract

```txt
new game, delayed one day
  -> every country missing state version 7
  -> refresh US-17

save load, delayed one day
  -> every country missing state version 7 or below version 7
  -> refresh US-17

covered trade-efficiency privilege activated or revoked
  -> coalesce same-day requests
  -> delayed country refresh after one day

monthly country pulse
  -> unchanged authoritative fallback
```

## Save compatibility

The migration must preserve the previous correction variables long enough for the PR #204 refresh to reconstruct the non-CBP baselines. It must not clear the old values before reconstruction.

Countries already at state version `7` are a no-op during game-start/load migration.

## Privilege coverage

The injection set is derived from the current Burghers and Nobles privilege files. Any privilege containing one of these modifier keys requires both activation and deactivation scheduling hooks:

```txt
selling_efficiency
import_efficiency
export_efficiency
merchant_maintenance_efficiency
```

Database injection is required; the original privilege definitions must not be replaced solely to add lifecycle effects.

## Acceptance criteria

```txt
- game start schedules the guarded migration after one day;
- game load schedules the guarded migration after one day;
- missing and pre-v7 country state is refreshed;
- v7 country state is skipped by the global migration;
- relevant privilege activation schedules one delayed refresh;
- relevant privilege revocation schedules one delayed refresh;
- multiple same-day requests are coalesced per country;
- the existing PR #204 calculation remains the only formula implementation;
- monthly refresh remains the fallback for conditional and temporary sources;
- CI derives privilege injection coverage from the current privilege definitions.
```
