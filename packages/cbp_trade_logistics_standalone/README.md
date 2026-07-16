# CBP Trade Logistics

Standalone implementation of US-17 and US-20.

The package runs one country-scoped `every_trade` pass from
`monthly_country_pulse`. It reads the Vanilla route and trade-owner values,
applies the US-17 money reconciliation with `add_gold`, and applies the US-20
delivery delta to the Vanilla destination market with `add_goods_supply`.

It deliberately contains no:

- No Void Economy dependency;
- Community Mod Manager integration;
- country x market stock accounting;
- promoted-market branch;
- persistent gameplay state.

Do not enable this package together with No Void Economy. NVE already contains
the US-17/US-20 route pass, so loading both would reconcile each route twice.
