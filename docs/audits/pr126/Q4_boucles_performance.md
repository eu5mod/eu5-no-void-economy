# Q4 — Loops and performance

## Conclusion

The main cost comes from country↔market↔goods loops, validation/reconciliation, and future trade traversal. The performance target is not only to reduce one loop: it must make the scopes that own heavy work explicit. The target model is therefore:

1. lightweight preparation by countries/markets;
2. heavy local work only once per promoted market, present countries, and active goods;
3. a separate country-scope trade pass that handles only trades assigned to the current country and delegates stock effects to handlers.

There is no separate Target E in the recommended design. Earlier generic market/trade Target E wording was removed because it blurs the ownership split: market-local work belongs under the promoted-market dispatcher or owner guard, while trade work belongs under the country-scope trade-owner pass.

## Audited loops

| Loop / flow | Trigger | Frequency | Traversed scope | Cache used | Performance risk | Target optimization |
|---|---|---|---|---|---|---|
| Country-market capacity refresh | Monthly cycle + capacity hooks | Monthly / event | Countries, present markets | `cbp_stock_cap_by_market`, country location pool | Medium | Read the country location pool; do not rescan per market/good |
| Promoted-market candidate registration | Monthly country prep | Monthly | Country → markets present in country | `cbp_promoted_markets_this_cycle` / candidate work list | Medium if repeated without ownership rules | Candidate discovery may happen per country, but stock-affecting local work must be once per promoted market |
| US-00 production | Promoted-market local branch | Monthly | Promoted market → present countries → active goods | per-good/market ledgers | High if all-good/all-location global | Wire under once-per-promoted-market owner surface and active-good filters |
| Stock admission | After production | Monthly | Produced country×market×good records | stock/cap maps | Medium | Keep per-good batch through generated adapters |
| US-10.1 consumption resolution | Monthly cycle or demand | Monthly | Requested country/market/good | stock maps + consumption ledgers | Medium | Same-market consumption only |
| US-10.2 transfers | Trade/demand phase | Monthly/on demand | Country → assigned trades, then handler scopes | sparse supplier cache / active markets | High if duplicated across countries or treated as market-local | Use country-scoped trade iteration only from the owning country and let handlers resolve add/remove/transfer consequences |
| Aggregate validation/rebuild | End of monthly/annual/audit cycle | Monthly/annual/debug | Active markets, present countries, active goods | active market lists, country-present cache | High | Rebuild `countries_present_in_market` once per promoted market |
| Reconciliation | Divergence or strict audit | Exceptional/diagnostic | Market countries for one good | country stock source | Very high if global | Trigger on divergence, strict init/yearly, or explicit test |
| Debug/probes | Test events | Manual | Targeted scopes | debug variables | Low outside tests | Keep in core_tests package |
| CMM callbacks | Main menu/runtime callback | Rare | Configuration variables | CMM variables | Low | No economic scan |

## Exact reconciliation cases to keep

1. Annual rebuild or explicitly requested strict audit.
2. Monthly validation detecting a divergence between market aggregate and the sum of country stocks.
3. Targeted test/debug event.
4. Controlled migration/init if the current schema requires it.

Reconciliation must not become the normal mechanism for recalculating country stocks from market stock.

## Canonical performance notation

| Symbol | Meaning |
|---|---|
| `C` | number of countries traversed by a full monthly pulse |
| `M_c` | average number of markets present in a country |
| `M` | total number of markets |
| `P` | number of promoted markets after normal/performance filtering and de-duplication |
| `K_m` | average number of countries present in a promoted market |
| `G_supported` | total goods supported by generated adapters |
| `G_market` | candidate or produced goods in a given market |
| `G_a` | active goods in a promoted market after filters/cache |
| `T_country` | trade candidates assigned to one country for the separate country-scope trade pass |

`G_market = 60` can remain a market-level load assumption. It is not the total number of goods supported by the mod: a Chinese, African, or European market will not necessarily have the same set of produced or active goods.

## Orchestration comparison

| Solution | Dominant shape | Order of magnitude | Reading | Risk |
|---|---|---|---|---|
| Current state country + broad pipelines | `monthly_country_pulse` -> country-markets capacity -> US-00 all-goods -> separate US-10 | `O(C * M_c + C * M_c * G_market + resolver scans)` | Costly baseline; several US may revisit the same axes | caches prepared outside the market/trade container |
| Ownership-split target | country prep -> promoted-market local branch -> country-scope trade pass | `O(C * M_c) + O(P * K_m * G_a) + O(C * T_country)` | Recommended target: explicit market-local owner and explicit trade owner | requires a robust promotion definition, owner guard, and trade-owner definition |

## Expected order of magnitude

Without profiling EU5 directly, a reasonable sizing is:

| Situation | Current broad state | Ownership-split target | Expected gain |
|---|---:|---:|---:|
| Small campaign / few active goods | tens of thousands of logical monthly iterations | a few thousand plus trade pass cost | `~5x` to `~20x` on market-local work |
| Medium campaign with many markets but few human-relevant markets | hundreds of thousands to a few million | tens of thousands plus trade pass cost | `~10x` to `~100x` on market-local work |
| Large campaign / strict audit / all-goods | several million, plus rescans by US | hundreds of thousands if `P << M`, plus trade pass cost | `~10x` to `~50x`; less if everything is promoted |
| Well-filtered Performance Mode | still costly if broad pipelines do not all respect the same filter | `P * K_m * G_a` for local work, plus country-scope trade pass | potentially `~100x` on goods/local branches; trade cost depends on assignment density |

The key point is that `P` must remain much smaller than `M` in Performance Mode, and `G_a` must remain smaller than `G_market` thanks to active-good lists. The trade pass is intentionally not filtered down to a promoted market: it must be country-scoped and assignment-gated to avoid double accounting and to keep future trade systems such as US-17 and US-20 visible. If Normal Mode promotes all current-country markets, the gain is mostly maintainability/cache ownership rather than spectacular runtime reduction, but it still prevents each US from rebuilding its own world.

## Review sizing assumption

```txt
G_market = 60 candidate / produced goods per market
M = 100 markets
C = 800 countries
P_normal = 100 retained/promoted markets
P_performance = 5 likely retained/promoted markets
K_m = 40 countries present in a promoted market
G_a = 10 active goods in a promoted market
T_country = assigned trade candidates for one country
```

### Raw comparison

| Scenario | Normal, 100 markets | Performance, 5 markets | Reading |
|---|---:|---:|---|
| Current | `800 * 100 * 60 = 4,800,000` | `4,800,000` if broad pipelines remain all-axis | worrying baseline |
| Ownership-split target | `80,000 prep + 100 * 40 * 10 + C*T_country` | `80,000 prep + 5 * 40 * 10 + C*T_country` | buys shared local cache and explicit trade ownership |

### Refined comparison

With `K_m = 40` present countries and `G_a = 10` active goods:

| Scenario | Refined formula | Logical iterations | Gain vs current |
|---|---:|---:|---:|
| Current | `C * M * G_market` | `4,800,000` | `1x` |
| Ownership-split target, normal | `C * M prep + P_normal * K_m * G_a + C*T_country` | `80,000 + 40,000 + C*T_country` | `~40x` before trade pass cost |
| Ownership-split target, performance | `C * M prep + P_performance * K_m * G_a + C*T_country` | `80,000 + 2,000 + C*T_country` | `~58x` before trade pass cost |

## Tick-time interpretation

If the current ModeU5 monthly tick is about 5 seconds and the broad loop cost is the dominant cost, the refined sizing gives this rough upper-bound estimate before trade-pass and engine overhead:

```txt
normal target:      5s * 120,000 / 4,800,000 ≈ 0.125s
performance target: 5s *  82,000 / 4,800,000 ≈ 0.085s
```

That is the optimistic loop-only estimate, not a promise for the whole EU5 tick. A safer practical estimate is:

| Assumption | Approximate optimized tick |
|---|---:|
| ModeU5 broad loop is almost all of the 5s tick | `~0.2s` to `~0.8s` |
| ModeU5 broad loop is about half of the 5s tick | `~2.5s` to `~3.0s` |
| Vanilla/engine overhead already consumes most of the 5s tick | much smaller visible gain |

Use this as an order-of-magnitude planning estimate until profiling counters measure the actual share of time spent in ModeU5 loops, engine overhead, and trade handlers.

## Design decision

The promoted-market local target is preferable because it makes `P`, `K_m`, and `G_a` explicit for heavy local work. The country-scope trade pass remains separate because `every_trade` is confirmed on country scope and should process assigned trades once, not as a market-local iterator. Even when the full cost includes a preparation phase and trade pass, this creates shared context for US-00, US-10, validation, debug, and future US without double-counting market-local mutations.

## Performance checklist for agents

```txt
1. What is the owning outer loop?
2. Is this country prep, once-per-promoted-market local work, or country-scope trade work?
3. Is the market discovered, promoted, and owned for local mutation?
4. Is the good supported, produced in this market, or active after filtering?
5. Is countries_present_in_market rebuilt exactly once for the promoted market?
6. Does the change add a new broad monthly scan?
7. Is the cache being used a source, derived cache, work cache, or debug state?
8. Does any trade loop stay country-scoped and assignment-gated?
```
