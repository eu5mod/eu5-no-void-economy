# TEST-US-17 - Operation-aware trade-profit reconciliation

## Objective

Validate that US-17:

```txt
- cancels native Import, Export, Selling, and Merchant Maintenance Efficiency;
- selects Import Efficiency for import routes and Export Efficiency for exports;
- transfers trade_operation_efficiency + Selling Efficiency to maintenance;
- uses no reciprocal or division;
- preserves negative combined efficiency;
- caps positive combined efficiency at MERCHANT_MAINTENANCE_COST;
- remains stable across repeated refreshes;
- applies one route-local treasury delta before the unchanged US-20 goods path.
```

## Fast preparation without regeneration

US-17 does not change generated Vanilla overrides. When the checkout already
contains the intended generated artifacts, validate and install directly:

```sh
python3 tools/validate_ci_static_contracts.py
./tools/validate_cbp_script_safety.sh
git diff --check
git diff --cached --check

./tools/install_local_packages.sh --skip-generate
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Use `./tools/dev_prepare_game.sh` only after changing configuration, a
generator, a CBG rule, a Vanilla-derived source, or a generated output.

## Focused arithmetic probe

Start EU5, load a campaign, and run:

```txt
event cbp_us17_owner_modifiers.1
```

Wait one in-game day for the delayed live-modifier check. Expected marker:

```txt
ModeU5 TEST PASS scenario=us17_trade_owner_modifiers hard_failures=0 operation_input=import_or_export_by_Trade.IsExport native_inputs_cancelled=selling_import_export_maintenance maintenance=cancelled_then_route_delta clamp=merchant_maintenance_cost_define negative_efficiency=preserved idempotence=passed live_auto_modifier_application=passed cmm_gate=open
```

The detailed checks must include:

```txt
import: I=0.05 Ex=0.10 S=0.02 -> trade_operation_efficiency=0.05, C=0.07
export: I=0.05 Ex=0.10 S=0.02 -> trade_operation_efficiency=0.10, C=0.12
native cancellations: Import=-0.05, Export=-0.10, Selling=-0.02, Maintenance=-0.08
negative: I=-0.40 S=-0.20 -> C=-0.60, with no lower clamp
upper cap: Ex=2 S=1 -> C=MERCHANT_MAINTENANCE_COST
idempotence: a second calculation reconstructs all four original baselines
```

## Runtime validation

1. Use a country that owns at least one import route and one export route.
2. Record its Import, Export, Selling, and Merchant Maintenance Efficiency.
3. Let one monthly tick run and confirm four localized CBP modifiers are shown.
4. Confirm all four effective native inputs are zero after CBP cancellation.
5. Confirm an import uses `Ei`, while an export uses `Ex`, in the detailed US-17
   operation-aware diagnostics.
6. Confirm `C = min(trade_operation_efficiency + S, D)` and the treasury delta
   is `D * C`, where `D = NCountry.MERCHANT_MAINTENANCE_COST`.
7. Let a second monthly tick run without changing inputs. Corrections and route
   results must not drift.
8. Change a policy or government reform and confirm the shared refresh updates
   all four baselines.
9. Save, reload, let one monthly tick run, and confirm the same values remain.
10. Run the US-20 focused and combined probes to confirm goods loss is unchanged.

## Failure conditions

Reject the run for any of these:

```txt
an export route uses Import Efficiency
Import and Export Efficiency are both applied to one route
fewer or more than four native CBP modifiers
division by zero or reciprocal behavior
negative C clamped to zero
different correction after an unchanged second refresh
more than one US-17 treasury mutation per owned route
US-20 goods-reconciliation regression
script-system, unset-variable, or invalid-modifier error
```
