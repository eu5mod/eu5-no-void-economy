# TEST-US-17 - Native trade-profit reconciliation

## Objective

Validate that US-17:

```txt
- cancels native import and selling price-margin efficiencies;
- transfers their summed effect to merchant maintenance;
- uses no reciprocal or division;
- preserves negative combined efficiency;
- caps positive combined efficiency at MERCHANT_MAINTENANCE_COST;
- remains stable across repeated refreshes;
- leaves treasury accounting to Vanilla.
```

## Fast preparation without regeneration

US-17 does not change generated Vanilla overrides. When the checkout already
contains the intended generated artifacts, validate and install them directly:

```sh
python3 tools/validate_ci_static_contracts.py
./tools/validate_cbp_script_safety.sh
git diff --check
git diff --cached --check

./tools/install_local_packages.sh --skip-generate
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Use `./tools/dev_prepare_game.sh` instead only after changing `.env`, a
generator, a CBG rule, a Vanilla-derived source, or a generated output. That
command already generates twice, validates, installs, checks the installation,
and clears logs; do not surround it with duplicate preparation commands.

## Focused arithmetic probe

Start EU5, load a campaign, and run:

```txt
event cbp_us17_owner_modifiers.1
```

Expected log marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 mode=native_auto_modifiers combination=sum_without_division clamp=merchant_maintenance_cost_define negative_efficiency=preserved idempotence=passed treasury_reconciliation=none
```

The detailed checks must include:

```txt
positive:    I=0.10 S=0.05 M=0.20 -> corrections=-0.10/-0.05/-0.05
negative:    I=-0.40 S=-0.20 M=0.20 -> C=-0.60, final maintenance factor=1.60
upper cap:   I=1.40 S=1.20 -> C=MERCHANT_MAINTENANCE_COST
idempotence: a second calculation reconstructs the original baselines
```

## Native runtime validation

1. Record one owned route's displayed profit and the country's Import
   Efficiency, Selling Efficiency, and Merchant Maintenance Efficiency.
2. Let one monthly tick run. Confirm the three visible CBP reconciliation
   modifiers exist on the country.
3. Confirm effective Import and Selling Efficiency are zero after the CBP
   corrections.
4. Confirm the maintenance correction equals `C - M`, where
   `C = min(I + S, MERCHANT_MAINTENANCE_COST)`, and effective maintenance
   efficiency equals `C`.
5. Let a second monthly tick run without changing inputs. Values and route
   profit must not drift.
6. Change a policy and a government reform. Confirm the corrections refresh
   after the engine applies each change.
7. Obtain or console-grant a research modifier. Confirm the monthly fallback
   incorporates it on the next monthly tick.
8. Save, reload, let one monthly tick run, and confirm the same values remain.
9. Run the US-20 focused and combined reconciliation probes to confirm goods
   loss remains unchanged.

## Failure conditions

Reject the run for any of these:

```txt
division by zero or reciprocal behavior
negative C clamped to zero
different correction after an unchanged second refresh
live US-17 add_gold mutation
missing or untranslated auto-modifier
US-20 goods-reconciliation regression
script-system, unset-variable, or invalid-modifier error
```
