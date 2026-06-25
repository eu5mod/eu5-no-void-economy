# US-18 — Optionalité à la carte via CMF/CMM et intégration log / saving / audit

Labels: `module:core`, `integration:cmf`, `type:configuration`, `perf`

## User Story

```txt
US-18 — Optionalité à la carte via CMF/CMM et intégration log / saving / audit
```

As a player and ModeU5 maintainer, I want No Void Economy to expose its gameplay, performance, debug, audit, and persistence services à la carte through the Community Mod Framework / CMM surface, so that a campaign can choose the right gameplay and diagnostic profile without disabling the required Core package, silently changing package activation, or corrupting persistent stock state.

## Functional objective

Register No Void Economy as a CMF/CMM-integrated product and expose configurable services as explicit à-la-carte settings.

The story must distinguish:

```txt
CMF dependency:
  required integration dependency for the product configuration surface

à-la-carte optionality:
  per-service settings exposed by NVE through CMF/CMM
```

The CMF/CMM configuration surface must drive script-safe runtime modes for:

```txt
NVE core behavior profile
Goods decay service
Debug messages
Monthly stock consistency check / audit mode
Accounting persistence / save mode
Planned balance and trade services
```

The integration must not imply that Core can be disabled while ModeU5 is active. It must also not imply that package-level optional companions can be enabled or removed mid-campaign.

## Module / availability

```txt
Package: No Void Economy
Activation: required Core package with required CMF dependency
Optionality model: à-la-carte product services exposed through CMF/CMM settings
Behavior when CMF is absent:
  unsupported playset / install state
  do not emulate CMF flags
  do not synthesize CMM registration
  fail closed to safe defaults where unset flags are read
```

Default service posture:

```txt
NVE main profile: Active / performance-oriented default
Debug messages: Off
Monthly stock check: Off
Save mode: Light / minimal persistence
In-development services: visible only as planned/disabled/no-op where applicable
```

## Runtime position

```txt
Campaign setup:
  CMF/CMM registers NVE tabs, groups, settings, and callbacks.

Initialization:
  CMM setting flags are read by Core configuration initialization.
  Runtime mode flags and persistence policy flags are derived once from selected settings.

Monthly step:
  Debug/audit/save-mode gates are read by monthly systems.
  Full stock validation is allowed only when audit mode is active.
  Full US-00 diagnostic ledger persistence is allowed only in strict, debug, audit, or human-relevant persistence modes.

Yearly step:
  Existing yearly validation and diagnostic behavior continue to read the same debug/audit gates.

Depends on counters from:
  none

Feeds counters / gates to:
  US-00 diagnostic ledger persistence
  US-10 / UI monthly counters where applicable
  stock consistency validation
  debug and audit tooling
  persistent-state audit validation
```

## Required scopes / values / effects

| Need                            | Scope                                 | Candidate                                                                                                                                         | Status    | TECH-01 ID |
| ------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ---------- |
| CMF registration hook           | country / CMF registration on_action  | `cmf_on_mod_registration` → `nve__on_register_cmf_mod` → `nve__register_cmf_mod`                                                                  | TO_TEST   | CMF        |
| CMF callback hook               | country / CMF callback on_action      | `cmf_on_callback` → `nve__on_cmf_callback` → `nve__handle_cmf_callback`                                                                           | TO_TEST   | CMF        |
| Register dropdown settings      | country                               | `cmm_register_dropdown_setting` for NVE main profile, debug messages, monthly stock check, save mode, balance difficulty                          | TO_TEST   | CMF        |
| Register bool settings          | country                               | `cmm_register_bool_setting` for decay, trade cost, planned balance/rebel/subject services                                                         | TO_TEST   | CMF        |
| Expose scripted GUI callbacks   | country                               | `cmm_add_scripted_gui` plus `*_on_changed` handlers                                                                                               | TO_TEST   | CMF        |
| Read CMM setting values         | global / country-owned CMM map access | `variable_map(cmm|flag:<setting>)`                                                                                                               | TO_TEST   | CMF        |
| Main NVE service flag           | CMM setting map                       | `no_void_economy__nve_no_void_economy_main` plus alias sync for `activate_no_void_economy`                                                        | TO_TEST   | CMF        |
| Debug mode                      | global runtime flags                  | `modeu5_enter_normal_runtime_mode`, `modeu5_enter_debug_runtime_mode`, `modeu5_debug_level`                                                       | CONFIRMED | internal   |
| Audit mode                      | global runtime flags                  | `modeu5_enter_audit_runtime_mode`, `modeu5_audit_enabled_trigger`, `modeu5_full_validation_allowed_trigger`                                       | CONFIRMED | internal   |
| Accounting persistence policy   | global runtime flags                  | `modeu5_enter_minimal_accounting_persistence`, `modeu5_enter_human_relevant_accounting_persistence`, `modeu5_enter_strict_accounting_persistence` | CONFIRMED | internal   |
| Human-relevant full ledger gate | global variable list / market scope   | `modeu5_performance_relevant_markets`, `modeu5_human_relevant_full_ledger_market_trigger`                                                         | CONFIRMED | internal   |
| Slow-mode player warnings       | country event                         | `nve_cmm_warning.*` events for slow audit/save settings                                                                                           | TO_TEST   | CMF        |

## Persistent storage / variable-map contract

US-18 does not own stock, capacity, production, consumption, or void-economy source-of-truth maps.

It owns only configuration-derived scalar runtime mode flags and reads CMF/CMM setting flags.

```txt
logical dimensions:
  product service setting
  runtime mode
  persistence policy

logical record and fields:
  CMM service flag:
    setting id
    selected value

  runtime mode:
    modeu5_runtime_mode_normal
    modeu5_runtime_mode_debug
    modeu5_runtime_mode_audit
    modeu5_debug_level

  accounting persistence:
    modeu5_accounting_persistence_minimal
    modeu5_accounting_persistence_human_relevant
    modeu5_accounting_persistence_strict

owner scope:
  CMF/CMM owns setting variable maps
  ModeU5 Core owns derived scalar runtime flags

tuple/key:
  CMM setting flag key
  no additional country × market × good key owned by this US

confirmed physical map family:
  external CMF/CMM setting maps read through variable_map(cmm|flag:<setting>)
  no new ModeU5 stock/capacity map family

physical value type:
  numeric selected index / boolean flag
  scalar global variables for derived mode flags

default value:
  debug off
  audit off
  minimal/light save mode
  planned services disabled or no-op

write owner:
  CMF/CMM writes setting flags
  ModeU5 configuration initialization writes derived Core runtime flags

readers:
  configuration triggers
  debug triggers
  audit validation triggers
  US-00 ledger persistence gates
  performance / human-relevant market helpers

reset/rebuild lifecycle:
  runtime mode flags are cleared before setting the selected mode
  accounting persistence flags are cleared before setting the selected policy
  human-relevant market list is rebuilt only when the human-relevant policy needs a current monthly scope list
```

Rules:

* Do not duplicate CMF/CMM settings into independent ModeU5 UI shadow maps.
* Do not make diagnostic persistence fields authoritative gameplay state.
* Do not mutate stock, capacity, market aggregate, production penalty, or demand-resolution state from CMM callbacks.
* Do not use CMF/CMM settings to pretend that a missing optional companion package is loaded.
* Do not use CMF/CMM settings to promise that a static override can be enabled or removed mid-campaign.
* Missing or unset CMM values must fall back to safe default behavior.

## Files expected to change

```txt
.metadata/metadata.json
docs/generated_issues/us-18-cmf-cmm-a-la-carte-services-log-saving-audit.md
in_game/common/on_action/nve__cmm_on_actions.txt
in_game/common/scripted_effects/nve__cmm_effects.txt
in_game/common/scripted_guis/nve__cmm_scripted_gui.txt
in_game/common/scripted_effects/modeu5_configuration_effects.txt
in_game/common/scripted_triggers/modeu5_configuration_triggers.txt
in_game/common/scripted_effects/modeu5_performance_effects.txt
main_menu/localization/english/nve__cmm_l_english.yml
docs/technical/MODULE_OPTION_MODEL.md
docs/technical/PERSISTENT_STATE_AUDIT.md
tools/audit_modeu5_persistent_state.sh
tools/validate_module_packages.sh
```

## Dependencies

```txt
Depends on:
  CORE-00 module/package contract
  CMF/CMM dependency metadata
  MODULE_OPTION_MODEL
  PERF-16 persistent-state audit
  PERF-17 minimal US-00 carryover record
  PERF-19 human-relevant full-ledger policy
  PERF-20 migration/audit/validation guardrails

Blocks:
  Stable public configuration profile for NVE
  Player-facing à-la-carte service selection
  Safe future service toggles for planned trade/balance/rebel/subject features

Related US:
  US-00
  US-01
  US-02
  US-03
  US-10
  US-11
  US-18-UI, if split later
```

## Implementation rules

* CMF is a required integration dependency for this product surface; do not describe CMF itself as optional.
* Optionality means each exposed NVE service has a selectable state, default state, and no-effect or fail-closed behavior.
* The Core package remains required while ModeU5 is active.
* Package-level optional companions remain launcher/playset concerns, not CMM runtime toggles.
* Do not create a separate custom configuration system outside CMF/CMM for these product services.
* CMM callbacks may warn, sync aliases, or update configuration flags, but must not mutate stock directly.
* All stock mutations remain restricted to centralized stock effects.
* Debug, audit, and strict/full-ledger persistence are diagnostic modes; they must not change economic results.
* Save mode controls persistence breadth, not whether authoritative stock/capacity/penalty state exists.
* Minimal/light save mode must preserve gameplay carryover fields and clear or ignore retired diagnostic fields.
* Human-relevant save mode may persist full diagnostic ledger fields only for markets relevant to human-played countries, unless debug/audit/strict mode is active.
* Complete/strict save mode must be visibly marked as slower and diagnostic-heavy.
* Monthly stock check must be visibly marked as slower and must enable audit/full validation gates only through approved triggers.
* In-development services must remain no-op or invalid until their implementing US exists.
* All user-facing options must have localization and warning text where performance impact is expected.
* Validation must catch stale generated helpers, missing persistence gates, and accidental clearing of authoritative maps.

## US-specific boundary checks

* [ ] CMF is treated as a dependency, not as an optional package.
* [ ] À-la-carte optionality is expressed at service-setting level.
* [ ] Core NVE gameplay is not disabled by pretending the required package is absent.
* [ ] CMM settings do not manufacture optional companion package markers.
* [ ] CMM settings do not enable or remove static package overrides mid-campaign.
* [ ] CMM callbacks do not directly mutate stock, capacity, market aggregate, production penalty, or demand-resolution maps.
* [ ] Debug/audit/strict modes do not alter economic formulas or stock conservation.
* [ ] Save mode changes persistence breadth only.
* [ ] Slow settings are visible and warned to the player.
* [ ] Planned features are marked as in development and remain no-op/invalid until implemented.
* [ ] Default profile remains performance-safe for normal gameplay.

## Acceptance criteria

* [ ] NVE registers itself with CMF/CMM through the shared mod registration on_action.
* [ ] NVE registers the expected tabs, groups, dropdown settings, bool settings, and scripted GUI entries.
* [ ] NVE callback handling routes recognized CMM setting changes to explicit handlers.
* [ ] Unknown or unsupported callbacks do not mutate ModeU5 gameplay state.
* [ ] Default CMM values produce safe defaults: debug off, audit off, minimal/light persistence, planned services disabled/no-op.
* [ ] Debug Messages = Basic enables basic debug state and `modeu5_debug_level = 1`.
* [ ] Debug Messages = Detailed enables verbose debug state and `modeu5_debug_level = 2`.
* [ ] Monthly Stock Check = On enables audit/full-validation gates and shows a slow-mode warning.
* [ ] Save mode = Light selects minimal accounting persistence.
* [ ] Save mode = Balanced selects human-relevant full-ledger persistence.
* [ ] Save mode = Complete selects strict full-ledger persistence and shows a slow-mode warning.
* [ ] Minimal/light persistence keeps authoritative gameplay carryover fields and does not persist non-authoritative full US-00 diagnostic ledger fields after normal monthly processing.
* [ ] Human-relevant persistence persists full diagnostic ledger fields only for human-relevant markets, unless debug/audit/strict mode is active.
* [ ] Strict/debug/audit modes can still persist full diagnostic ledger fields for validation.
* [ ] Migration/cleanup guardrails never clear authoritative stock maps.
* [ ] Migration/cleanup guardrails never clear shared capacity maps.
* [ ] Migration/cleanup guardrails never clear production penalty carryover or the active-record marker.
* [ ] Static validation fails if generated helpers lose required persistence gates.
* [ ] Static validation fails if generated helpers clear authoritative maps during retired-ledger cleanup.
* [ ] Localization exists for all exposed CMM options and slow-mode warnings.
* [ ] `error.log` has no new blocking error after a controlled runtime smoke test.
* [ ] Documentation and generated issue files are updated.

## Manual test scenario

### Setup

```txt
Package set:
  No Void Economy Core
  Community Mod Framework dependency installed
  Optional companion packages unchanged from the selected test playset

Country:
  Any human-played country

Campaign:
  Disposable test campaign

Relevant CMF/CMM parameters:
  NVE main profile
  Debug Messages
  Monthly Stock Check
  Save mode
  Planned service toggles
```

### Static checks

```sh
./tools/generate_all.sh
./tools/audit_modeu5_persistent_state.sh
./tools/validate_module_packages.sh
git diff --check
./tools/install_local_packages.sh --check
```

### Runtime smoke matrix

```txt
Scenario A — Defaults
  Debug Messages = Off
  Monthly Stock Check = Off
  Save mode = Light

Expected:
  runtime mode = normal
  debug level = 0
  audit/full validation gate = off
  accounting persistence = minimal
  no full diagnostic ledger persistence in normal monthly runtime
  no new blocking error.log entry

Scenario B — Debug + audit + balanced save
  Debug Messages = Basic
  Monthly Stock Check = On
  Save mode = Balanced

Expected:
  runtime mode includes debug behavior
  debug level = 1
  audit/full validation gate = on
  accounting persistence = human-relevant
  human-relevant market list is rebuilt for the month
  full diagnostic ledger is available for human-relevant markets
  non-human-relevant markets remain minimal unless debug/audit gate applies
  slow monthly stock check warning is shown

Scenario C — Detailed logs + complete save
  Debug Messages = Detailed
  Monthly Stock Check = On
  Save mode = Complete

Expected:
  runtime mode includes verbose debug behavior
  debug level = 2
  audit/full validation gate = on
  accounting persistence = strict
  full diagnostic ledger may persist globally for validation
  complete save warning is shown
  no stock/capacity/penalty authoritative map is cleared by persistence cleanup
```

### Expected debug / audit output

```txt
Detected CMF/CMM integration state
Selected NVE service flags
Derived runtime mode
Derived debug level
Derived audit/full-validation gate
Derived accounting persistence policy
Human-relevant market rebuild count when applicable
US-00 full-ledger persistence allowed/blocked reason
Stock validation result when audit is enabled
No new blocking error.log entry
```

## Known limitations

* This US describes CMF/CMM integration as a required product dependency plus à-la-carte service optionality; it does not make CMF optional.
* Changing package selection mid-campaign remains unsupported.
* C
