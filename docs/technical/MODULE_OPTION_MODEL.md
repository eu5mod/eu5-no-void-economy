# ModeU5 module and option model

## Decision

ModeU5 is distributed as one required core package, three optional gameplay companion packages, and one testing-only companion package.

The required package is not a toggle. Calling it an option such as "Deactivate Void Economy" creates a misleading double negative because the player cannot disable it while using ModeU5. Use the positive package name:

```txt
No Void Economy
```

The package matrix is:

| Package | Availability | User stories |
|---|---|---|
| No Void Economy | Required | CORE-00, CORE-01.1 through CORE-01.6, CORE-02, CORE-03, EPIC US-00, US-00.1 through US-00.4, US-00-UI, US-01, US-01-UI, US-02, US-02-UI, US-03, US-03-UI, EPIC US-10, US-10.0 through US-10.3, US-10-UI, US-11 |
| Rebalance Economy | Optional; included in the recommended playset | US-04, US-04-UI, US-05, US-05-UI, US-08, US-08-UI, US-09, US-09-UI |
| Rebalance Estate Power | Optional; included in the recommended playset | US-07, US-07-UI |
| Rebalance Early Blobbing | Optional; included in the recommended playset | US-13, US-14 |
| No Void Economy Tests | Optional; testing-only, excluded from normal campaign playsets | Deterministic CORE-01 debug events, stock-operator helpers, and controlled Core engine-exposure probes such as TECH-01 `091` |

## Recommended playset

The supported default campaign profile is the full gameplay suite:

```txt
No Void Economy
+ Rebalance Economy
+ Rebalance Estate Power
+ Rebalance Early Blobbing
```

Here, optional means that a gameplay companion may be removed in the launcher before campaign start. It does not mean that the recommended campaign profile omits it. The separate `No Void Economy Tests` package is not a gameplay companion; enable it only in dedicated validation sessions.

Core cannot load a missing companion's files and must never manufacture its package marker. Selecting the four gameplay launcher entries activates the recommended campaign profile.

## Campaign lifecycle contract

The package set is fixed for the lifetime of a campaign. Loading an existing
save with the same package set is supported. Adding or removing a package from
that save is not.

| Package | Lifecycle-sensitive content | Add to an existing save | Remove from an existing save |
|---|---|---|---|
| No Void Economy | Start-game schema initialization and persistent stock state | Unsupported | Unsupported |
| Rebalance Economy | Runtime US-04/05/09 systems plus planned static US-08 definitions | Unsupported | Unsupported |
| Rebalance Estate Power | Planned static US-07 building definitions | Unsupported | Unsupported |
| Rebalance Early Blobbing | Planned static US-13 CB/wargoal definitions; currently marker-only while the cost hook remains blocked | Unsupported | Unsupported |
| No Void Economy Tests | Deterministic debug events and test-only helpers; no campaign content | Unsupported for normal campaigns | Remove by using a non-test playset before starting a normal campaign |

This restriction is package-level, even where one individual story could
technically be evaluated at runtime:

- package presence/version markers are written by `on_game_start`, not
  rediscovered when an existing save is loaded;
- removing a package does not remove its persistent marker or clean up
  package-owned state already stored in the save;
- static building, RGO, CB, and wargoal definitions are loaded with the active
  mod set and have no confirmed save-migration contract;
- no package currently defines the migration and cleanup needed to change that
  set safely.

The four gameplay package roots currently contain package descriptors and start-game
markers. The testing-only package contains deterministic debug events and helpers instead of gameplay state markers. The lifecycle rule is established now so later story implementations
cannot accidentally promise unsupported mid-campaign activation.

The source repository stores the companions under:

```txt
packages/modeu5_economy_rebalance/
packages/modeu5_trade_rebalance/
packages/modeu5_war_rebalance/
packages/modeu5_core_tests/
```

EU5 discovers local packages as sibling mod directories, not as selectable
children of one loaded package. `tools/install_local_packages.sh` publishes the
root Core payload, the three gameplay companion roots, and the testing-only package root as sibling local mods and records
their source branch and commit in `MODEU5_SOURCE.txt`.

The installer does not edit launcher playset state. The player must refresh the
launcher and enable the four gameplay entries in the recommended campaign playset once. Enable `No Void Economy Tests` only in a dedicated validation playset.

Each optional companion declares this metadata relationship:

```json
{
  "rel_type": "dependency",
  "id": "modeu5_core",
  "display_name": "No Void Economy (NVE)",
  "resource_type": "mod",
  "version": "0.1.*"
}
```

The controlled launcher test confirms:

```txt
enable one companion
-> compatible Core is enabled automatically

disable Core while companions are selected
-> companions remain selected; deactivation does not cascade

enable Core alone
-> optional companions remain unselected
```

The launcher still presents package roots as sibling mods. Dependency metadata does not
turn them into visually nested entries. The testing-only package is a fifth sibling entry when installed, but it is excluded from normal campaign playsets.

Do not make Core depend on the three companions. That would make the optional
packages mandatory and create dependency cycles because each companion already
depends on Core.

If one-click activation of the recommended profile becomes worthwhile, add a
separate metadata-only `ModeU5 Full Suite` package that depends on Core and all
three companions. Such a package would simplify initial activation but would
not be expected to cascade-disable its dependencies.

Each package's `.metadata/metadata.json` starts its short description with a
campaign-lifecycle warning. Local EU5 GUI files confirm that this description
is displayed in both the available-mod and selected-playset tooltips. This is
the supported warning surface under TECH-01 `107`; it informs the player but
does not technically prevent an unsafe package-set change.

## Why packages are the source of truth

Local EU5 files confirm:

```txt
main_menu/common/game_rules/
has_game_rule
```

Custom game rules can therefore select scripted runtime behavior.

However, US-07 and US-08 change static building/RGO definitions and numeric price or modifier fields loaded before gameplay. No reviewed engine documentation or vanilla example confirms that an active game-rule setting can conditionally replace those static numeric fields.

Therefore:

- do not promise one runtime checkbox that can disable US-07 or US-08 safely;
- do not load a static override and merely hide its UI when its option is off;
- use companion packages as the authoritative activation boundary;
- game rules may configure behavior wholly controlled by scripted triggers, such as debug output, but they must not contradict package activation.

## Package dependencies

```txt
Rebalance Economy        -> must be selected with No Void Economy
Rebalance Estate Power   -> must be selected with No Void Economy
Rebalance Early Blobbing -> must be selected with the matching No Void Economy version
```

US-13 has no stock-accounting dependency, but its companion package still belongs to the matching Core release so the suite has one version and support contract.

Launcher dependency activation is confirmed under TECH-01 `103`. Non-cascading
deactivation means the playset requirement and startup version diagnostic
remain mandatory: metadata cannot undo static overrides already loaded from an
invalid companion-only playset.

## Behavior when a package is absent

### Core

Core is always active when ModeU5 is active. There is no supported mode with:

```txt
ModeU5 loaded
ModeU5 stock/void-economy core disabled
```

Core initialization, centralized stock effects, stock resolution, decay, void-economy correction, validation, and mandatory debug remain enabled.

### Rebalance Economy

When absent:

- US-04 does not change local Pop-demand multipliers;
- US-05 leaves the vanilla Economic Base formula untouched;
- US-08 installs no building or RGO price override;
- US-09 applies no `+5%` Production Efficiency compensation;
- their UI/debug stories must report the module as absent or remain hidden;
- Core demand-outcome counters may still exist because US-10.3 owns them.

### Rebalance Estate Power

When absent:

- US-07 installs no trade-building balance override;
- vanilla trade-building values remain unchanged;
- US-02 remains part of Core and still owns ModeU5 storage-capacity calculations;
- no US-07-UI tooltip or localization may claim rebalanced values.

### Rebalance Early Blobbing

When absent:

- US-13 installs or selects no ModeU5 conquest-cost variant;
- US-14 installs or selects no autonomous rebel-demand replacement;
- vanilla CB/wargoal behavior remains unchanged.
- vanilla rebel independence-demand behavior remains unchanged.

## Configuration surfaces

ModeU5 configuration occurs before campaign start:

```txt
launcher/mod playset
  -> select all four gameplay packages for the recommended campaign profile
  -> remove Rebalance Economy, Rebalance Estate Power, or
     Rebalance Early Blobbing before campaign start when desired
  -> add No Void Economy Tests only for dedicated validation sessions

EU5 Game Rules
  -> configure script-safe settings owned by loaded packages
```

Core currently defines one native game rule:

```txt
ModeU5 Debug Output = Off / Basic / Verbose
```

The selected setting initializes `modeu5_debug_level` when the campaign starts. It is not an in-game toggle.

Do not create a custom in-game configuration panel. In particular, no configuration surface may:

- disable Core stock gameplay;
- pretend that a game rule unloads a companion package;
- imply that an unloaded static override can be enabled after startup;
- imply that removing a loaded companion restores vanilla static definitions in the current process;
- rerun fresh stock seeding;
- call a stock mutation outside the centralized effects.

## Save and multiplayer rules

- Package selection occurs in the launcher before starting or loading a campaign.
- A source checkout is not itself the launcher choices; publish the package roots with `tools/install_local_packages.sh`.
- Use `tools/install_local_packages.sh --check` to verify the branch and commit currently installed.
- Adding or removing an optional package during an existing campaign is unsupported unless a dedicated migration is implemented and tested.
- All multiplayer participants must use the same package set and versions.
- Debug output must list the detected ModeU5 packages and versions.
- A missing required Core selection is an unsupported playset and must be reported prominently.

## Implementation boundary

Packaging and option behavior must be implemented before optional balance stories.

Package presence markers are package-owned:

```txt
Core:
  modeu5_core_package_loaded
  modeu5_core_package_version

Economy companion:
  modeu5_economy_rebalance_loaded
  modeu5_economy_package_version

Trade companion:
  modeu5_trade_rebalance_loaded
  modeu5_trade_package_version

War companion:
  modeu5_war_rebalance_loaded
  modeu5_war_package_version
```

Package version variables are numeric runtime compatibility codes. Release
`0.1.0` uses compatibility code `100`; the human-readable release remains in
each `descriptor.mod` and `.metadata/metadata.json`.

Do not add module checks inside the six centralized stock effects. The Core package owns those effects unconditionally.

For a valid playset, optional package code must fail closed:

```txt
package absent
-> no optional mutation
-> no optional static override
-> no stale optional modifier
-> no misleading optional UI
```
