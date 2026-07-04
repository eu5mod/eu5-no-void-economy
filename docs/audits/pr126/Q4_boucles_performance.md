# Q4 — Loops and performance

## Conclusion

The main cost comes from country↔market↔goods loops, validation/reconciliation, and future trade traversal. The performance target is not only to reduce one loop: it must make the scopes that own heavy work explicit. The target model is therefore:

1. lightweight preparation by countries/markets;
2. heavy local work only once per promoted market, present countries, and active goods;
3. a separate country-scope trade pass that handles only trades assigned to the current country and delegates stock effects to handlers.

## Audited loops

| Loop / flow | Trigger | Frequency | Traversed scope | Cache used | Performance risk | Target optimization |
|---|---|---|---|---|---|---|
| Country-market capacity refresh | Monthly cycle + capacity hooks | Monthly / event | Countries, present markets | `modeu5_stock_cap_by_market`, country location pool | Medium | Read the country location pool; do not rescan per market/good |
| Promoted-market candidate registration | Monthly country prep | Monthly | Country → markets present in country | `modeu5_promoted_markets_this_cycle` / candidate work list | Medium if repeated without ownership rules | Candidate discovery may happen per country, but stock-affecting local work must be once per promoted market |
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
| Generic market/trade Target E | readiness -> market/trade outer loop -> B/C/D under E | `O(P? * (K_m + G_a + T?))` | Good only if selector E is already restricted | too abstract if promotion and trade ownership are not explicit |
| Ownership-split target | country prep -> promoted-market local branch -> country-scope trade pass | `O(C * M_c) + O(P * K_m * G_a) + trade pass cost` | Best compromise: explicit market-local owner and explicit trade owner | requires a robust promotion definition and owner guard |

## Expected order of magnitude

Without profiling EU5 directly, a reasonable sizing is:

| Situation | Current broad state | Ownership-split target | Expected gain |
|---|---:|---:|---:|
| Small campaign / few active goods | tens of thousands of logical monthly iterations | a few thousand plus trade pass cost | `~5x` to `~20x` on market-local work |
| Medium campaign with many markets but few human-relevant markets | hundreds of thousands to a few million | tens of thousands plus trade pass cost | `~10x` to `~100x` on market-local work |
| Large campaign / strict audit / all-goods | several million, plus rescans by US | hundreds of thousands if `P << M`, plus trade pass cost | `~10x` to `~50x`; less if everything is promoted |
| Well-filtered Performance Mode | still costly if broad pipelines do not all respect the same filter | `P * G_a` for local work, plus country-scope trade pass | potentially `~100x` on goods/local branches; trade cost depends on assignment density |

The key point is that `P` must remain much smaller than `M` in Performance Mode, and `G_a` must remain smaller than `G_market` thanks to active-good lists. The trade pass is intentionally not filtered down to a promoted market: it must be country-scoped and assignment-gated to avoid double accounting and to keep future trade systems such as US-17 and US-20 visible. If Normal Mode promotes all current-country markets, the gain is mostly maintainability/cache ownership rather than spectacular runtime reduction, but it still prevents each US from rebuilding its own world.

## Review sizing assumption

```txt
G_market = 60 candidate / produced goods per market
M = 100 markets
C = 800 countries
P_normal = 100 retained/promoted markets
P_performance = 5 likely retained/promoted markets
T_country = assigned trade candidates for one country
```

### Raw comparison

| Scenario | Normal, 100 markets | Performance, 5 markets | Reading |
|---|---:|---:|---|
| Current | `800 * 100 * 60 = 4,800,000` | `4,800,000` if broad pipelines remain all-axis | worrying baseline |
| Generic Target E | `100 * 800 * 60 = 4,800,000` | `5 * 800 * 60 = 240,000` | good only if E already receives the filter and does not double-count trade |
| Ownership-split target | `80,000 prep + 100 * 800 * 60 + trade pass` | `80,000 prep + 5 * 800 * 60 + trade pass` | buys shared local cache and explicit trade ownership |

### Refined comparison

With `K_m = 40` present countries and `G_a = 10` active goods:

| Scenario | Refined Performance formula | Logical iterations | Gain vs current |
|---|---:|---:|---:|
| Current | `C * M * G_market` | `4,800,000` | `1x` |
| Generic Target E | `P * K_m * G_a` if E is already filtered | `5 * 40 * 10 = 2,000` | theoretical `2,400x`, but incomplete without the trade pass |
| Ownership-split target | `C * M prep + P * K_m * G_a + trade pass` | `80,000 + 2,000 + trade pass` | `~58x` before trade pass cost; trade remains explicit and non-duplicated |

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
