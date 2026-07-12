# ModeU5 Wealth Endpoint

## Purpose

Expose a reusable read-only wealth snapshot for downstream ModeU5 systems without
adding another `every_owned_location` traversal.

## Runtime placement

The endpoint is refreshed inside the existing monthly CORE-04 country-location
memory pass:

```txt
monthly_country_pulse
  -> modeu5_core04_refresh_current_country_location_market_memory
    -> every_owned_location
```

The pass already visits every owned location to remember its current market. The
wealth calculation is fused into that same iterator.

## Formula

For a location with positive control:

```txt
location_tax_base = location_wealth * local_control
location_wealth   = tax_base / local_control
```

The reusable scripted value is:

```txt
modeu5_location_wealth_endpoint
```

It reads `tax_base` and `local_control` from location scope.

## Persistent endpoints

Location scope:

```txt
cbp_location_wealth_endpoint
cbp_location_wealth_endpoint_stamp
```

Country scope:

```txt
cbp_country_wealth_endpoint
cbp_country_wealth_endpoint_stamp
cbp_country_wealth_unresolved_location_count
```

`cbp_country_wealth_endpoint` is a country-owned scalar. It must not be replaced
with a global variable, because `monthly_country_pulse` runs independently for
every country and a global singleton would be overwritten by the last country
processed.

## Zero-control boundary

When `local_control <= 0`, tax base contains no information from which the
underlying location wealth can be recovered. The endpoint therefore:

- stores zero for that location;
- excludes it from the country total;
- increments `cbp_country_wealth_unresolved_location_count`.

Downstream systems that require a complete value must check the unresolved count
before treating the country endpoint as exact. Do not divide by an arbitrary
control floor, because that would fabricate wealth.

## Downstream contract

A country-scoped consumer may read:

```txt
var:cbp_country_wealth_endpoint
var:cbp_country_wealth_unresolved_location_count
var:cbp_country_wealth_endpoint_stamp
```

A location-scoped consumer may read:

```txt
var:cbp_location_wealth_endpoint
var:cbp_location_wealth_endpoint_stamp
```

The endpoint is observational only. It must not directly mutate vanilla wealth,
tax base, control, stock, Estate income, or treasury income.
