# US-17 - Native trade-profit reconciliation

## Business rule

Import and Selling Efficiency no longer alter the two price margins directly.
Their combined value changes merchant maintenance instead, while Vanilla keeps
ownership of route profit, AI decisions, UI display, and treasury posting.

For the non-CBP country baselines `I`, `S`, and `M`:

```txt
C = min(I + S, 1)

CBP import correction      = -I
CBP selling correction     = -S
CBP maintenance correction = C - M
```

This cancels the native price effects and replaces the native maintenance
efficiency `M` with `C`. The resulting maintenance factor is `1 - C`. The
configured `define:NCountry|MERCHANT_MAINTENANCE_COST` remains part of the
native monetary base and must not replace the unitless `1` or enter the additive
percentage correction.

The sum is not averaged. It has no lower clamp. Negative efficiency therefore
increases maintenance, and there is no reciprocal that could divide by zero.

## Runtime placement

```txt
monthly_country_pulse(country)
  -> cbp_run_monthly_country_trade_owner_cycle
     -> cbp_refresh_us17_native_profit_modifiers_for_current_country
     -> every_trade
        -> capture trade owner and route quantity
        -> cbp_run_us20_route_loss_reconciliation
           -> US-20 received-goods reconciliation only
```

Policy and reform on-actions call the same country refresh. Monthly execution
is the authoritative fallback for research and other modifier sources.

## Baseline reconstruction

Because country `modifier:*` reads include the active CBP auto-modifiers, each
refresh first subtracts its previous persisted corrections. It then calculates
and stores new corrections from the reconstructed non-CBP values. This makes
the operation idempotent and safe on repeated monthly ticks and save reloads.

## Ownership and boundaries

```txt
US-17 owner: current country in the country trade-owner pass
US-17 money mutation: native engine only
US-17 add_gold: forbidden in the live wrapper
US-20 owner: route-local reconciliation
US-20 stock mutation: unchanged centralized stock/goods path
```

The historical seeded route-money effects remain test scaffolding only. They
must never be called from the production monthly country pass.

## Acceptance contract

```txt
- native import correction cancels the reconstructed import baseline;
- native selling correction cancels the reconstructed selling baseline;
- maintenance correction uses C - M so effective maintenance efficiency is C;
- C is the sum without division, capped only above one;
- negative C remains negative;
- repeated refreshes do not drift;
- policy and reform hooks use the shared refresh;
- monthly refresh occurs once before every_trade;
- production US-17 performs no add_gold mutation;
- US-20 route-loss reconciliation remains active;
- all three auto-modifiers have visible localization.
```

## Focused test

Run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 mode=native_auto_modifiers combination=sum_without_division clamp=maximum_only negative_efficiency=preserved idempotence=passed treasury_reconciliation=none
```

Full runtime protocol:

```txt
docs/tests/TEST-US-17-owner-modifier-inputs.md
```
