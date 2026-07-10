# TEST-US-17 — Trade-owner modifier inputs and maximum-only cap

## Objective

Validate the live US-17 input contract:

```txt
buying_efficiency          <- trade owner country modifier
selling_efficiency         <- trade owner country modifier
merchant_maintenance_cost  <- trade owner country modifier
```

The buying/selling average is capped only above `1`:

```txt
average_efficiency = min((buying_efficiency + selling_efficiency) / 2, 1)
```

There is deliberately no lower clamp. Negative efficiency remains negative and
therefore increases maintenance instead of being silently converted to zero.

## Formula covered by the deterministic probe

```txt
maintenance_factor = 1 + merchant_maintenance_cost

adjusted_base_maintenance =
    base_maintenance_amount * maintenance_factor

maintenance_saving =
    adjusted_base_maintenance * average_efficiency

route_money_delta =
    -old_price_side_bonus
    + maintenance_saving
```

The probe uses seeded route prices and base maintenance because those route-safe
engine reads remain a separate TECH-01 boundary. The country modifier reads are
live reads from `c:FRA` during the probe.

## Run

Install the current branch and clear logs, then run:

```txt
event modeu5_us17_owner_modifiers.1
```

Choose:

```txt
Run owner modifier probe
```

## Expected result

Visible event option:

```txt
PASS — owner modifiers and maximum-only cap
```

Expected log marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=buying_selling_merchant_maintenance clamp=maximum_only
```

The probe validates:

```txt
1. Captured buying_efficiency equals FRA.modifier:buying_efficiency.
2. Captured selling_efficiency equals FRA.modifier:selling_efficiency.
3. Captured merchant_maintenance_cost equals FRA.modifier:merchant_maintenance_cost.
4. (-0.4 + -0.2) / 2 remains -0.3.
5. (1.4 + 1.2) / 2 is capped from 1.3 to 1.
6. With base maintenance 20 and merchant maintenance cost 0.20:
     maintenance factor = 1.20
     adjusted base maintenance = 24
     average efficiency = 0.15
     maintenance saving = 3.60
7. With old price-side bonus 35:
     route money delta = -31.40
```

## Post-run grep

```sh
grep -R -E "us17_trade_owner_modifiers|US17 OWNER_MODIFIERS|ASSERT FAIL|Tried to localize with localization disabled|Failed to fetch variable|Cannot read" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs" || true
```

Expected absence:

```txt
ASSERT FAIL
Tried to localize with localization disabled
Failed to fetch variable
Cannot read
```

## Remaining boundary

This probe confirms the country modifier input layer and the formula arithmetic.
It does not confirm live route reads for:

```txt
sell price
buy price
export cost modifier
base maintenance amount
trade-route profit write surface
country trade-income accounting surface
```

Until those surfaces are confirmed, the live route-money path remains fail-closed
after successfully capturing the three country modifiers.
