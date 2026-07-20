# CBP Trade Profit

A deliberately small standalone implementation of the **US-17 trade-balance
rules validated in #204**.

## Business rule

The mod reconstructs the non-CBP country values before every refresh:

```txt
S  = Selling Efficiency
I  = Import Efficiency
Ex = Export Efficiency
M  = Merchant Maintenance Efficiency
```

Selling retains a diminishing negative residual:

```txt
C = 0.05 / (1 + 10*S)

Selling correction = -S - C
effective Selling Efficiency = -C
```

Import and Export no longer amplify absolute market-price margins:

```txt
Import correction = -I
Export correction = -Ex

effective Import Efficiency = 0
effective Export Efficiency = 0
```

Their value is redirected into the same reciprocal maintenance rule as #204:

```txt
effective Merchant Maintenance Efficiency =
    1 - 1 / (1 + M/2 + 5*(I + Ex))

Maintenance correction =
    effective Merchant Maintenance Efficiency - M
```

The current effective values already include the previous month's standalone
corrections. Each refresh subtracts those stored corrections first, recovering
the non-CBP baselines and preventing monthly drift.

## Engine trade-balance Defines

The standalone also carries the registered EU5 engine overrides used by the
validated trade-balance package:

```txt
NCountry.MERCHANT_MAINTENANCE_COST = 0.5
NMarket.MIN_PRICE_IMPACT = -0.68
NMarket.MAX_PRICE_IMPACT = 2.16
```

`MERCHANT_MAINTENANCE_COST` is increased from the Vanilla value of `0.25`.
The market price bounds provide the wider CBP trade-price range.

These are genuine engine-defined keys. The four coefficients used by the US-17
formula remain named script values because arbitrary custom `CBP_*` Define keys
are not a supported runtime value surface.

## Light-product boundary

This product contains only the country-level trade-profit balance:

- four country auto-modifiers;
- four named script constants;
- one registered engine-Define file for maintenance cost and price bounds;
- one calculation/reconstruction effect file;
- monthly, policy-change, and reform-change refresh hooks;
- English localization and mod metadata.

It deliberately contains **no** route iteration, `add_gold`, goods loss, market
or stock mutation, US-20 implementation, CMM integration, NVE lifecycle,
country × market accounting, GUI, events, generators, or optional CBP balance
packages.

The full CBP project uses the same Selling coefficient as a source for US-20
physical goods loss. This light standalone stops at the US-17 country modifier
surface.

Do not enable this standalone together with No Void Economy while NVE contains
the same US-17 modifiers or the same trade Defines; both products would apply
the balance changes.

## Arithmetic fixture

With:

```txt
S = 0.10
I = 0.20
Ex = 0.30
M = 0.08
```

the expected values are:

```txt
C = 0.05 / (1 + 0.10*10) = 0.025

Selling correction = -0.125
effective Selling = -0.025

Import correction = -0.20
Export correction = -0.30

maintenance denominator = 1 + 0.08/2 + 5*(0.20 + 0.30) = 3.54
effective maintenance = 1 - 1/3.54 = 0.717514
maintenance correction = 0.717514 - 0.08 = 0.637514
```

The validated Venice example also gives:

```txt
M = 0.40
I = 0
Ex = 0.035

effective maintenance = 1 - 1/1.375 = 0.272727
maintenance correction = -0.127273
```

which corresponds to the observed `-12.72%` tooltip value within game
precision.

## Install

Place this repository folder in the EU5 user `mod` directory and enable
**CBP Trade Profit** in its own playset. No dependency, generation, or
configuration step is required.

## Runtime check

1. Enable only **CBP Trade Profit**.
2. Start or load a campaign and advance one monthly tick.
3. Confirm the four localized CBP modifiers are present.
4. Confirm Import and Export Efficiency are zero.
5. Confirm Selling Efficiency equals the negative diminishing coefficient, not
   zero.
6. Confirm Merchant Maintenance follows the reciprocal formula above.
7. Advance two unchanged monthly ticks and verify that values do not drift.
8. Change a relevant policy or government reform and verify that the baselines
   refresh.
9. Check `error.log` for unknown Define keys, unset variables, or invalid
   modifier/script-value reads.
