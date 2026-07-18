# TECH-01 addendum - US-17 operation-aware trade-profit inputs

## Purpose

Record the production US-17 accounting surface after correcting the origin-side
efficiency rule. Vanilla applies the directional efficiency to the source-market
purchase cost. Import and export operations do not use the same country input:

```txt
trade_operation_efficiency = import_efficiency
trade_operation_efficiency = export_efficiency when Trade.IsExport
```

With `Q` as moved goods, `Ps` as source price, `Pd` as destination price,
`S` as Selling Efficiency, `M` as Merchant Maintenance Efficiency, `D` as the
base route-maintenance cost, and `T` as sound tolls, the confirmed Vanilla
starting point is:

```txt
Vanilla profit = Q * Pd * (1 + S)
               - Q * Ps * (1 - trade_operation_efficiency)
               - D * (1 - M)
               - T
```

The distinction can only be evaluated from trade scope. A country may own both
imports and exports in the same month, so one country-wide maintenance modifier
cannot represent both route results.

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope | Status |
|---|---|---|---|
| Import efficiency | `modifier:import_efficiency` | country | Confirmed |
| Export efficiency | `modifier:export_efficiency` | country | Confirmed |
| Selling efficiency | `modifier:selling_efficiency` | country | Confirmed |
| Merchant maintenance efficiency | `modifier:merchant_maintenance_efficiency` | country | Confirmed |
| Operation direction | `is_export` / `Trade.IsExport` | trade | Confirmed |

The tested build rejects `modifier:buying_efficiency` and
`modifier:merchant_maintenance_cost`. They must not appear in executable code.

## Formula

Let the current non-CBP country baselines be:

```txt
I = import_efficiency
E = export_efficiency
S = selling_efficiency
M = merchant_maintenance_efficiency
D = define:NCountry|MERCHANT_MAINTENANCE_COST

trade_operation_efficiency = I for an import operation
trade_operation_efficiency = E for an export operation
C = min(trade_operation_efficiency + S, D)
C_country = min(I + E + S, D)
```

CBP applies four additive auto-modifier corrections:

```txt
import correction      = -I
export correction      = -E
selling correction     = -S
maintenance correction = C_country - M
C_country = min(-selling correction - import correction - export correction, D)
```

The three native price-margin inputs become zero. Merchant Maintenance
Efficiency becomes `C_country`, not zero. Country auto-modifiers cannot evaluate
`Trade.IsExport`, so the country-visible reference values Selling, Import, and
Export Efficiency together. From the existing country-owned `every_trade` pass,
each route then removes the non-directional part of that reference:

```txt
import treasury delta = D * (C_import - C_country)
export treasury delta = D * (C_export - C_country)
final maintenance     = D * (1 - C_route)
```

There is no division and no lower clamp on `C`. Negative operation or selling
efficiency therefore remains meaningful and increases effective maintenance.
Positive sums are capped by the loaded define `D`.

## Why route reconciliation is required

EU5 exposes `Trade.IsExport` to GUI and `is_export` to trade-scope script, but
does not expose a trade-scope modifier that can replace country Import or Export
Efficiency inside the native profit calculation. The price inputs can be
cancelled natively, and the native maintenance modifier can represent the
country-level sum of Selling, Import, and Export Efficiency. Neither directional
route result can be represented by that same country modifier when the country
owns routes in both directions.

The exact financial result therefore uses the already existing monthly
country-owned trade loop and `add_gold`. This correction affects treasury but is
not represented in Vanilla route-profit UI or AI projection. This limitation is
preferable to silently applying Import Efficiency to export operations.

US-20 remains a separate goods-only follow-up in the same loop. It does not
apply US-17 money a second time.

## Idempotent refresh

Auto-modifier values are included in `modifier:*` reads. Before recalculating,
the shared refresh subtracts all four previously persisted corrections from the
effective values. This reconstructs the current non-CBP baselines and prevents
drift across monthly, policy, and reform refreshes.

Refresh surfaces remain:

```txt
on_policy_changed -> cbp_country_governance_changed
on_reform_change  -> cbp_country_governance_changed
monthly country trade-owner pass
```

Governance hooks refresh baselines only. Financial reconciliation remains owned
by the monthly trade pass, preventing duplicate payments after a law or reform
change.

## Runtime probe

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 operation_input=import_or_export_by_Trade.IsExport native_price_inputs_cancelled=selling_import_export maintenance=country_all_efficiencies_plus_route_delta maintenance_formula=verified
```

The probe uses distinct Import and Export Efficiency fixtures, validates both
operation paths, the upper cap, negative efficiency, four-way idempotence, and
the live application of all four auto-modifiers. The delayed check derives its
expected effective maintenance independently from the persisted CBP Selling,
Import, and Export corrections, then compares it with
`modifier:merchant_maintenance_efficiency`.
