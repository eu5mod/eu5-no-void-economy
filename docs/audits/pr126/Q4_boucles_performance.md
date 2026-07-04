# Q4 — Loops and performance

## Conclusion

The main cost comes from country↔market↔goods loops and from validation/reconciliation. The performance target is not only to reduce one loop: it must make the scopes that own heavy work explicit. The target model is therefore: lightweight preparation by countries/markets, then heavy work only on promoted markets, present countries, active goods, and relevant demands.

## Audited loops

| Loop / flow | Trigger | Frequency | Traversed scope | Cache used | Performance risk | Target optimization |
|---|---|---|---|---|---|---|
| Country-market capacity refresh | Monthly cycle + capacity hooks | Monthly / event | Countries, present markets | `modeu5_stock_cap_by_market`, country location pool | Medium | Read the country location pool; do not rescan per market/good |
| US-00 production | Monthly cycle | Monthly | Country → owned locations → tracked goods | per-good/market ledgers | High if all-good/all-location global | Wire under promoted market and active good |
| Stock admission | After production | Monthly | Produced country×market×good records | stock/cap maps | Medium | Keep per-good batch through generated adapters |
| US-10.1 consumption resolution | Monthly cycle or demand | Monthly | Requested country/market/good | stock maps + consumption ledgers | Medium | Same-market consumption only |
| US-10.2 transfers | Inter-market demands | Monthly/on demand | Candidate source markets | sparse supplier cache / active markets | High | Fast pruning before detailed scoring |
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
| `P` | number of markets promoted after human/performance filtering |
| `K_m` | average number of countries present in a promoted market |
| `G_supported` | total goods supported by generated adapters |
| `G_market` | candidate or produced goods in a given market |
| `G_a` | active goods in a promoted market after filters/cache |
| `T_m` | relevant inter-market demands/trades for the promoted market |

`G_market = 60` can remain a market-level load assumption. It is not the total number of goods supported by the mod: a Chinese, African, or European market will not necessarily have the same set of produced or active goods.

## Orchestration comparison

| Solution | Dominant shape | Order of magnitude | Reading | Risk |
|---|---|---|---|---|
| Current state country + broad pipelines | `monthly_country_pulse` -> country-markets capacity -> US-00 all-goods -> separate US-10 | `O(C * M_c + C * M_c * G_market + resolver scans)` | Costly baseline; several US may revisit the same axes | caches prepared outside the market/trade container |
| Generic market/trade Target E | readiness -> market/trade outer loop -> B/C/D under E | `O(P? * (K_m + G_a + T_m))` | Good if selector E is already restricted | too abstract if promotion is not explicit |
| Promoted-market target | `every_market_present_in_country` preparation -> promotion -> local branch + trade branch | `O(C * M_c) + O(P * (K_m * G_a + T_m))` | Best compromise: explicit, measurable, shared filter | requires a robust promotion definition and rebuild |

## Expected order of magnitude

Without profiling EU5 directly, a reasonable sizing is:

| Situation | Current broad state | Promoted-market target | Expected gain |
|---|---:|---:|---:|
| Small campaign / few active goods | tens of thousands of logical monthly iterations | a few thousand | `~5x` to `~20x` |
| Medium campaign with many markets but few human-relevant markets | hundreds of thousands to a few million | tens of thousands | `~10x` to `~100x` |
| Large campaign / strict audit / all-goods | several million, plus rescans by US | hundreds of thousands if `P << M` | `~10x` to `~50x`; less if everything is promoted |
| Well-filtered Performance Mode | still costly if broad pipelines do not all respect the same filter | `P * G_a` instead of `M * G_market` on heavy branches | potentially `~100x` on goods/trade branches |

The key point is that `P` must remain much smaller than `M` in Performance Mode, and `G_a` must remain smaller than `G_market` thanks to active-good lists. If Normal Mode promotes all current-country markets, the gain is mostly maintainability/cache ownership rather than spectacular runtime reduction, but it still prevents each US from rebuilding its own world.

## Review sizing assumption

```txt
G_market = 60 candidate / produced goods per market
M = 100 markets
C = 800 countries
P_normal = 100 retained/promoted markets
P_performance = 5 likely retained/promoted markets
```

### Raw comparison

| Scenario | Normal, 100 markets | Performance, 5 markets | Reading |
|---|---:|---:|---|
| Current | `800 * 100 * 60 = 4,800,000` | `4,800,000` if broad pipelines remain all-axis | worrying baseline |
| Generic Target E | `100 * 800 * 60 = 4,800,000` | `5 * 800 * 60 = 240,000` | good only if E already receives the filter |
| Promoted-market | `80,000 prep + 100 * 800 * 60 = 4,880,000` | `80,000 prep + 5 * 800 * 60 = 320,000` | buys a shared cache and avoids rescans |

### Refined comparison

With `K_m = 40` present countries and `G_a = 10` active goods:

| Scenario | Refined Performance formula | Logical iterations | Gain vs current |
|---|---:|---:|---:|
| Current | `C * M * G_market` | `4,800,000` | `1x` |
| Generic Target E | `P * K_m * G_a` if E is already filtered | `5 * 40 * 10 = 2,000` | theoretical `2,400x` |
| Promoted-market | `C * M prep + P * K_m * G_a` | `80,000 + 2,000 = 82,000` | `~58x` complete, `2,400x` on the heavy branch |

## Design decision

The promoted-market target is preferable because it makes `P`, `K_m`, and `G_a` explicit. Even when the full cost includes a preparation phase, that preparation creates shared context for US-00, US-10, validation, debug, and future US.

## Performance checklist for agents

```txt
1. What is the owning outer loop?
2. Is the market discovered or promoted?
3. Is the good supported, produced in this market, or active after filtering?
4. Is countries_present_in_market rebuilt exactly once?
5. Does the change add a new broad monthly scan?
6. Is the cache being used a source, derived cache, work cache, or debug state?
```
