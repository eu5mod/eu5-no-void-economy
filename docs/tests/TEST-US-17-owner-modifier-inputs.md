# TEST-US-17 — Trade-owner inputs, maintenance define, and maximum-only cap

## Objective

Validate the live US-17 input contract:

```txt
semantic buying efficiency      <- trade owner modifier:import_efficiency
selling efficiency              <- trade owner modifier:selling_efficiency
merchant maintenance efficiency <- trade owner modifier:merchant_maintenance_efficiency
base merchant maintenance cost  <- define:NCountry|MERCHANT_MAINTENANCE_COST
base route maintenance          <- trade_volume × loaded define
```

The literal modifier names `buying_efficiency` and `merchant_maintenance_cost`
are not valid modifier types in the tested EU5 build. The first is represented by
`import_efficiency`; the second concept is split between a base define and the
beneficial `merchant_maintenance_efficiency` country modifier.

The buying/selling average is capped only above `1`:

```txt
average_efficiency = min((import_efficiency + selling_efficiency) / 2, 1)
```

There is deliberately no lower clamp. Negative efficiency remains negative and
therefore increases maintenance instead of being silently converted to zero.

## Formula covered by the deterministic probe

```txt
base_maintenance_unit_cost =
    define:NCountry|MERCHANT_MAINTENANCE_COST

base_maintenance_amount =
    trade_volume * base_maintenance_unit_cost

merchant_maintenance_factor =
    max(0, 1 - merchant_maintenance_efficiency)

adjusted_base_maintenance =
    base_maintenance_amount * merchant_maintenance_factor

maintenance_saving =
    adjusted_base_maintenance * average_efficiency

route_money_delta =
    -old_price_side_bonus
    + maintenance_saving
```

The probe reads the loaded define directly, so it automatically validates the
value supplied by the active NVE define override rather than duplicating a
hardcoded base cost. Seeded route prices remain necessary because their
route-safe script surfaces are a separate TECH-01 boundary.

## Clean install and run

The installer now removes each existing `cbp_*` package directory before
copying. Pull the branch and install it:

```sh
./tools/generate_all.sh
./tools/validate_generators.sh
./tools/validate_module_packages.sh
python3 ./tools/validate_ci_static_contracts.py
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Then start EU5 and run:

```txt
event cbp_us17_owner_modifiers.1
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
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=import_selling_merchant_maintenance_efficiency base_cost=define_NCountry_MERCHANT_MAINTENANCE_COST clamp=maximum_only
```

The probe validates:

```txt
1. Captured semantic buying efficiency equals FRA.modifier:import_efficiency.
2. Captured selling efficiency equals FRA.modifier:selling_efficiency.
3. Captured maintenance efficiency equals FRA.modifier:merchant_maintenance_efficiency.
4. The base unit cost equals define:NCountry|MERCHANT_MAINTENANCE_COST.
5. Base maintenance equals trade_volume × the loaded define.
6. (-0.4 + -0.2) / 2 remains -0.3.
7. (1.4 + 1.2) / 2 is capped from 1.3 to 1.
8. With seeded base maintenance 20 and maintenance efficiency 0.20:
     maintenance factor = 0.80
     adjusted base maintenance = 16
     average efficiency = 0.15
     maintenance saving = 2.40
9. With old price-side bonus 35:
     route money delta = -32.60
```

## Post-run grep

Use only the freshly cleared current log files:

```sh
grep -E "us17_trade_owner_modifiers|US17 OWNER_MODIFIERS|ASSERT FAIL|Non-existent modifier type|Event target link 'modifier' returned an unset scope|Tried to localize with localization disabled|Failed to fetch variable|Cannot read" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/error.log" \
"$HOME/Documents/Paradox Interactive/Europa Universalis V/logs/debug.log" || true
```

Expected absence:

```txt
ASSERT FAIL
Non-existent modifier type
Event target link 'modifier' returned an unset scope
Tried to localize with localization disabled
Failed to fetch variable
Cannot read
```

## Remaining boundary

This probe confirms the country modifier input layer, the loaded maintenance
define, the `trade_volume × define` base amount, and the formula arithmetic.
It does not confirm live route reads or visible accounting surfaces for:

```txt
sell price
buy price
export cost modifier
trade-route profit write surface
country trade-income accounting surface
```

Until those surfaces are confirmed, the live route-money path remains
fail-closed after successfully capturing the owner modifiers and define-derived
base maintenance.
