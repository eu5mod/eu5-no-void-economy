# ModeU5 module and option model

## Decision

ModeU5 is distributed as one required core package and three optional companion packages.

The required package is not a toggle. Calling it an option such as "Deactivate Void Economy" creates a misleading double negative because the player cannot disable it while using ModeU5. Use the positive package name:

```txt
ModeU5 Core - Stock-Constrained Economy
```

The package matrix is:

| Package | Availability | User stories |
|---|---|---|
| ModeU5 Core - Stock-Constrained Economy | Required | CORE-00, CORE-01.1 through CORE-01.6, CORE-02, CORE-03, EPIC US-00, US-00.1 through US-00.4, US-00-UI, US-01, US-01-UI, US-02, US-02-UI, US-03, US-03-UI, EPIC US-10, US-10.0 through US-10.3, US-10-UI, US-11 |
| ModeU5 Economy Rebalance | Optional companion package | US-04, US-04-UI, US-05 family, US-05-UI, US-08, US-08-UI, US-09, US-09-UI |
| ModeU5 Trade Rebalance | Optional companion package | US-07, US-07-UI |
| ModeU5 War Rebalance | Optional companion package | US-13 |

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
- game rules may be added later for behavior wholly controlled by scripted triggers, but they must not contradict package activation.

## Package dependencies

```txt
ModeU5 Economy Rebalance -> must be selected with ModeU5 Core
ModeU5 Trade Rebalance   -> must be selected with ModeU5 Core
ModeU5 War Rebalance     -> must be selected with the matching ModeU5 Core version
```

US-13 has no stock-accounting dependency, but its companion package still belongs to the matching Core release so the suite has one version and support contract.

Automatic launcher/descriptor dependency enforcement remains `TO_TEST` under TECH-01 `103`. Until confirmed, the playset requirement and startup version diagnostic are mandatory, but startup script cannot undo static overrides that were already loaded from an invalid companion-only playset.

## Behavior when a package is absent

### Core

Core is always active when ModeU5 is active. There is no supported mode with:

```txt
ModeU5 loaded
ModeU5 stock/void-economy core disabled
```

Core initialization, centralized stock effects, stock resolution, decay, void-economy correction, validation, and mandatory debug remain enabled.

### Economy Rebalance

When absent:

- US-04 does not change local Pop-demand multipliers;
- US-05 leaves the vanilla Economic Base formula untouched;
- US-08 installs no building or RGO price override;
- US-09 applies no `+5%` Production Efficiency compensation;
- their UI/debug stories must report the module as absent or remain hidden;
- Core demand-outcome counters may still exist because US-10.3 owns them.

### Trade Rebalance

When absent:

- US-07 installs no trade-building balance override;
- vanilla trade-building values remain unchanged;
- US-02 remains part of Core and still owns ModeU5 storage-capacity calculations;
- no US-07-UI tooltip or localization may claim rebalanced values.

### War Rebalance

When absent:

- US-13 installs or selects no ModeU5 conquest-cost variant;
- vanilla CB/wargoal behavior remains unchanged.

## Save and multiplayer rules

- Package selection occurs in the launcher before starting or loading a campaign.
- Adding or removing an optional package during an existing campaign is unsupported unless a dedicated migration is implemented and tested.
- All multiplayer participants must use the same package set and versions.
- Debug output must list the detected ModeU5 packages and versions.
- A missing required Core selection is an unsupported playset and must be reported prominently.

## Implementation boundary

Packaging and option behavior must be implemented before optional balance stories.

Do not add module checks inside the six centralized stock effects. The Core package owns those effects unconditionally.

For a valid playset, optional package code must fail closed:

```txt
package absent
-> no optional mutation
-> no optional static override
-> no stale optional modifier
-> no misleading optional UI
```
