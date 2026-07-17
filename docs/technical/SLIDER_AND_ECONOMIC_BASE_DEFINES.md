# Slider and Economic Base defines

The Rebalance Economy package groups its Economic Base and expense-slider
defines in:

```txt
loading_screen/common/defines/cbp_slider_defines.txt
```

The file has one engine namespace, `NEconomy`, and two related policies.

## Economic Base redesign

CBP derives Economic Base from tax base and trade profit while disabling direct
population, trade-value, interest, foreign-building, and institution inputs.
Subject contribution remains at its Vanilla weight, and every country is
eligible for trade-based Economic Base.

## Economic Base proportional sliders

`COURT_SPENDING_FRACTON`, `DIPLOMATIC_SPENDING_FRACTION`,
`STABILIY_EXPENSE_FACTOR`, and `PRESTIGE_INVEST_FACTOR` determine the budget
weight of their sliders in proportion to Economic Base.

## Default slider decay

The separate investment factors control the monthly Stability and government
power movement produced by their sliders and retain the already documented
mandatory-expense tuning:

```txt
STABILITY_INVEST_FACTOR = 1
GOV_POWER_INVEST_FACTOR = 3.0
```

The source file records the corresponding Vanilla value beside every override.
The engine's historical define spellings, including `COURT_SPENDING_FRACTON`
and `STABILIY_EXPENSE_FACTOR`, must be preserved exactly.

## AI annexation consequence

Because the redesign gives countries stronger incentives to build and retain
Control, the same file raises the bordering-Control threshold used by AI subject
annexation:

```txt
NAI.AI_ANNEX_SUBJECT_BORDERING_CONTROL_NEEDED = 0.60
```

Economic Base, slider, and related AI defines must not be duplicated in the
legacy root `cbp_economic_defines.txt`; that file retains only unrelated economy
and Pop tuning.
