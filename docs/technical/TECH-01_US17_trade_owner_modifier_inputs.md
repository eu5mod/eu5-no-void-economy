# TECH-01 addendum — US-17 trade-owner and maintenance inputs

## Purpose

Record the runtime-correct US-17 input surface without confusing a base define,
country efficiency modifiers, and unresolved route accounting APIs.

This addendum should be folded into the numbered TECH-01 matrix during the next
matrix-wide maintenance pass.

## Confirmed owner scope

The modifier owner is the country saved from the trade-scope `owner` link:

```txt
scope:cbp_trade_owner_country
```

The monthly route loop enters that saved country scope before reading any
country modifier value. The scheduler country, market-center owner, source
market owner, and target market owner must not be substituted unless one of
them independently resolves to the saved trade owner.

## Correct engine exposures

| Need | Required scope | Exposure | Type | Status | Runtime use |
|---|---|---|---|---|---|
| Semantic buying efficiency | saved trade-owner country | `modifier:import_efficiency` | country modifier value | CONFIRMED | Captured into `cbp_trade_efficiency_buying_efficiency` |
| Selling efficiency | saved trade-owner country | `modifier:selling_efficiency` | country modifier value | CONFIRMED | Captured into `cbp_trade_efficiency_selling_efficiency` |
| Merchant maintenance efficiency | saved trade-owner country | `modifier:merchant_maintenance_efficiency` | country modifier value | CONFIRMED | Captured into `cbp_trade_efficiency_merchant_maintenance_efficiency` |
| Base merchant maintenance unit cost | script value | `define:NCountry|MERCHANT_MAINTENANCE_COST` | define value | CONFIRMED | Captured into `cbp_trade_efficiency_base_maintenance_unit_cost` |
| Base route maintenance | route trade context | `trade_volume × define:NCountry|MERCHANT_MAINTENANCE_COST` | derived value | CONFIRMED for controlled probe and live capture | Captured into `cbp_trade_efficiency_base_maintenance_amount` |
| Cap average efficiency above one | transaction-local numeric value | `max = 1` | script-value upper bound | CONFIRMED | No lower clamp; negative values remain negative |

The tested EU5 build rejects these former candidate names:

```txt
modifier:buying_efficiency
modifier:merchant_maintenance_cost
```

They produced `Non-existent modifier type`, unset modifier-scope, and `none`
value errors. They must not appear in executable script.

## Loaded define rule

The base cost is not duplicated in a scripted constant:

```txt
cbp_trade_base_merchant_maintenance_cost = {
  value = define:NCountry|MERCHANT_MAINTENANCE_COST
  min = 0
}
```

NVE already changes this define. Reading it at runtime therefore consumes the
effective loaded value from the active package set.

The route base amount is:

```txt
base_maintenance_amount =
    trade_volume
  * define:NCountry|MERCHANT_MAINTENANCE_COST
```

The moved-goods quantity remains a distinct value derived through the existing
literal-good transport-cost helper. It must not replace `trade_volume` in the
merchant-maintenance calculation.

## Maintenance formula

`merchant_maintenance_efficiency` is beneficial and reduces the base amount:

```txt
merchant_maintenance_factor =
    max(0, 1 - merchant_maintenance_efficiency)

adjusted_base_maintenance =
    base_maintenance_amount * merchant_maintenance_factor
```

The repurposed import/selling average then creates the additional saving:

```txt
average_efficiency =
    (import_efficiency + selling_efficiency) / 2

capped_average_efficiency =
    min(average_efficiency, 1)

maintenance_saving =
    adjusted_base_maintenance * capped_average_efficiency
```

EU5 bound-oriented syntax for the average deliberately contains:

```txt
max = 1
```

and deliberately omits:

```txt
min = 0
```

A negative average therefore creates a negative saving and an additional route
cost. The merchant-maintenance factor itself is lower-bounded at zero so a
country efficiency above 100% does not create negative base maintenance.

## Remaining route boundaries

The following still require route-safe script or accounting exposure:

```txt
sell price
buy price
export cost modifier
trade-route profit read/write surface
country trade-income accounting surface
```

The base maintenance amount is no longer in this blocked list because it is
derived from confirmed `trade_volume` and the loaded define.

The live route-money calculation must continue to fail closed when the remaining
price or accounting inputs are unavailable. Diagnostics must distinguish that
route-input block from the confirmed owner-modifier and maintenance-define layer.

## Runtime probe

```txt
event cbp_us17_owner_modifiers.1
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=import_selling_merchant_maintenance_efficiency base_cost=define_NCountry_MERCHANT_MAINTENANCE_COST clamp=maximum_only
```

The probe confirms direct owner-country modifier reads, the loaded define,
`trade_volume × define` base maintenance, negative-average preservation, the
upper cap of one, and maintenance-factor arithmetic.
