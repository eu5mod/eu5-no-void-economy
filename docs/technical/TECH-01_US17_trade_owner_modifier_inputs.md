# TECH-01 addendum — US-17 trade-owner modifier inputs

## Purpose

Record the confirmed ownership and script-value surface for the three country
modifiers used by US-17 without confusing them with unresolved route-specific
economic values.

This addendum should be folded into the numbered TECH-01 matrix during the next
matrix-wide maintenance pass.

## Confirmed owner scope

The modifier owner is the country saved from the trade-scope `owner` link:

```txt
scope:modeu5_trade_owner_country
```

The monthly route loop enters that saved country scope before reading any of the
three modifier values.

The following scopes must not be substituted:

```txt
scheduler country
market-center owner
source-market owner
target-market owner
```

unless one of them independently resolves to the saved trade owner.

## Exposure records

| Need | Required scope | Exposure | Type | Status | Basis | Runtime use |
| --- | --- | --- | --- | --- | --- | --- |
| Read buying efficiency | saved trade-owner country | `modifier:buying_efficiency` | modifier value | CONFIRMED | US-17 specification and documented country modifier-value surface | Captured into `modeu5_trade_efficiency_buying_efficiency` |
| Read selling efficiency | saved trade-owner country | `modifier:selling_efficiency` | modifier value | CONFIRMED | US-17 specification and documented country modifier-value surface | Captured into `modeu5_trade_efficiency_selling_efficiency` |
| Read trade maintenance modifier | saved trade-owner country | `modifier:merchant_maintenance_cost` | modifier value | CONFIRMED | Modifier-types documentation identifies `merchant_maintenance_cost` as country Trade Maintenance | Captured into `modeu5_trade_efficiency_merchant_maintenance_cost` |
| Cap average efficiency above one | transaction-local numeric value | `max = 1` | script-value upper bound | CONFIRMED | TECH-01 bound semantics and approved US-17 business rule | No `min = 0`; negative values remain negative |

## Script-value implementation

```txt
modeu5_trade_owner_buying_efficiency = {
  value = modifier:buying_efficiency
}

modeu5_trade_owner_selling_efficiency = {
  value = modifier:selling_efficiency
}

modeu5_trade_owner_merchant_maintenance_cost = {
  value = modifier:merchant_maintenance_cost
}
```

These values are valid only when evaluated in the saved trade-owner country
scope.

## Clamp contract

```txt
average_efficiency =
    (buying_efficiency + selling_efficiency) / 2

capped_average_efficiency =
    min(average_efficiency, 1)
```

EU5 bound-oriented syntax:

```txt
value = buying_efficiency
add = selling_efficiency
divide = 2
max = 1
```

Do not add:

```txt
min = 0
```

Examples:

```txt
0.15  -> 0.15
1.30  -> 1.00
-0.30 -> -0.30
```

## Maintenance formula

```txt
maintenance_factor =
    1 + merchant_maintenance_cost

adjusted_base_maintenance =
    base_maintenance_amount * maintenance_factor

maintenance_saving =
    adjusted_base_maintenance * capped_average_efficiency
```

A negative capped average produces a negative saving and therefore an additional
maintenance cost.

## Remaining unresolved route surfaces

Confirmation of the three country modifier values does not confirm the following
route-specific inputs or accounting surfaces:

```txt
sell price
buy price
export cost modifier
base maintenance amount
trade-route profit read/write surface
country trade-income accounting surface
```

The live route-money calculation must continue to fail closed when these inputs
are unavailable. Diagnostics must distinguish this route-input block from the now
confirmed country modifier layer.

## Runtime probe

```txt
event modeu5_us17_owner_modifiers.1
```

Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 owner_inputs=buying_selling_merchant_maintenance clamp=maximum_only
```

The focused probe confirms direct country modifier reads, negative-value
preservation, the upper cap of one, and maintenance-factor arithmetic.
