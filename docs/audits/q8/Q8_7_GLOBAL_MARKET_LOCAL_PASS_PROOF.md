# Q8.7 — global market-local pass proof

## Status

```txt
PROOF PR ONLY
NO LIVE DISPATCHER REPLACEMENT
NO STOCK MUTATION
```

Q8.7 validates whether the engine can run a native global market-local pass from a safe debug/test entry point.

The current live runtime still uses the market-center ownership workaround. This PR does not replace it.

## Probe shape

The test-package probe is:

```txt
modeu5_q8_probe_global_market_iterator_exposure
```

It proves the following shape:

```txt
every_market_in_world
  -> save current market as modeu5_q8_7_global_market_candidate
  -> deduplicate the market in modeu5_q8_7_global_market_seen_markets
  -> save current market as modeu5_market_country_cache_market
  -> call modeu5_rebuild_countries_present_in_market
  -> record rebuild/failure counters
```

This is stronger than the earlier raw iterator probe. It proves that market scope can be entered and can run the existing market-country work-cache rebuild surface.

## Counters

```txt
modeu5_test_q8_7_global_market_count
modeu5_test_q8_7_global_market_unique_count
modeu5_test_q8_7_global_market_duplicate_count
modeu5_test_q8_7_market_country_cache_rebuild_count
modeu5_test_q8_7_market_country_cache_failed_count
```

## Runtime scenario marker

The probe emits stable scenario markers:

```txt
ModeU5 TEST ENTERED scenario=q87_global_market_local_pass
ModeU5 TEST PASS scenario=q87_global_market_local_pass
ModeU5 TEST FAIL scenario=q87_global_market_local_pass
```

These markers avoid dynamic localization and are easier to summarize from logs.

## Guardrails

```txt
- Test package only.
- No stock mutation.
- No live monthly dispatcher replacement.
- No `every_trade` call from market scope.
- No new persistent source-of-truth cache.
- `modeu5_countries_present_in_market` remains a rebuilt work cache.
```

## Exit interpretation

A passing Q8.7 proof means:

```txt
The native market iterator can enter market scope and rebuild the market-country work cache.
```

It does not mean:

```txt
The live market-center workaround should be replaced immediately.
```

A later live replacement PR must still prove:

```txt
- equivalent economic results;
- reduced duplicate market-local work;
- preserved order: country prep -> market-local -> country trade -> validation;
- no market-scope trade iteration.
```
