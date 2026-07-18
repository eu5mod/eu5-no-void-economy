# TECH-01 addendum - US-17 native trade-profit modifiers

## Purpose

Record the production US-17 accounting surface. US-17 no longer reconstructs
route profit with script prices or applies a parallel `add_gold` correction.
It changes the native country modifier stack so Vanilla route selection, AI,
UI, and treasury accounting consume one result.

## Confirmed engine surfaces

| Business input | EU5 exposure | Scope | Status |
|---|---|---|---|
| Buying/import efficiency | `modifier:import_efficiency` | country | Confirmed |
| Selling efficiency | `modifier:selling_efficiency` | country | Confirmed |
| Merchant maintenance efficiency | `modifier:merchant_maintenance_efficiency` | country | Confirmed |

The tested build rejects `modifier:buying_efficiency` and
`modifier:merchant_maintenance_cost`. They must not appear in executable code.

## Division-free formula

Let the current non-CBP baselines be:

```txt
I = import_efficiency
S = selling_efficiency
M = merchant_maintenance_efficiency
D = define:NCountry|MERCHANT_MAINTENANCE_COST
C = min(I + S, 1)
```

CBP applies three additive auto-modifier corrections:

```txt
import correction      = -I
selling correction     = -S
maintenance correction = C - M
```

The effective native values become:

```txt
effective import efficiency  = 0
effective selling efficiency = 0
effective maintenance efficiency = C
effective maintenance factor     = 1 - C
```

There is no division and no lower clamp on `C`. A negative import/selling sum
therefore remains economically meaningful and increases merchant maintenance.
Only positive sums above one are capped.

The literal `1` represents the dimensionless 100% factor. `D` is a monetary
define and therefore must not replace it. Let `B` be the native route-maintenance
amount before merchant-maintenance efficiency, including `D`. The monetary
equivalence is:

```txt
Vanilla maintenance = B * (1 - M)
CBP target          = B * (1 - C)
effective native    = B * (1 - M - correction)

correction = C - M
```

The common monetary base `B` cancels when the additive percentage correction is
solved. Reading `D` remains appropriate in absolute-gold probes, but production
writes a native percentage modifier and must not multiply that modifier by `D`.

## Idempotent refresh

Auto-modifier values are included in `modifier:*` reads. Before recalculating,
the shared refresh subtracts its three previously persisted corrections from
the effective values. This reconstructs the current non-CBP baseline and
prevents drift across repeated monthly, policy, or reform refreshes.

Refresh surfaces:

```txt
on_policy_changed -> cbp_country_governance_changed
on_reform_change  -> cbp_country_governance_changed
monthly country trade-owner pass
```

The monthly refresh is authoritative and catches research, temporary modifiers,
and any source without a dedicated confirmed country on-action. The two
governance hooks deliberately share one callback and one CBP registration each;
future consumers must extend that shared dispatcher.

## Production boundary

The production country pass refreshes US-17 once before `every_trade`. The
route-local wrapper then performs US-20 goods reconciliation only. Production
US-17 must not call `add_gold`, read route prices, or maintain a second profit
ledger.

This is the preferred architecture whenever a native modifier is available:
cancel or transform the native input rather than reconciling its financial
consequence after Vanilla has already evaluated AI and UI state.

The older route-money effects remain only as a historical deterministic fixture
for combined US-17/US-20 regression coverage. They are not a live fallback.

## Runtime probe

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 mode=native_auto_modifiers combination=sum_without_division clamp=maximum_only negative_efficiency=preserved idempotence=passed treasury_reconciliation=none
```

The probe covers positive, negative, upper-cap, full-maintenance, and repeated
refresh arithmetic. In-game tooltip and route-profit checks remain required to
confirm that the tested EU5 build updates native auto-modifiers without delay.
