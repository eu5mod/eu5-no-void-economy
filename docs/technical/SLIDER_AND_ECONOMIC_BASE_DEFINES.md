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

## Expense sliders

CBP increases the budget weight of Court and Stability expenses, reduces the
weight of Diplomatic and Prestige spending, and retains the already documented
mandatory-expense tuning:

```txt
STABILITY_INVEST_FACTOR = 1
GOV_POWER_INVEST_FACTOR = 3.0
```

The source file records the corresponding Vanilla value beside every override.
The engine's historical define spellings, including `COURT_SPENDING_FRACTON`
and `STABILIY_EXPENSE_FACTOR`, must be preserved exactly.
