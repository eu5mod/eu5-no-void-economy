# Political Reward Rebalance

## Functional contract

The Rebalance Economy package adjusts political rewards to remain coherent
with the higher mandatory Stability and government-power investment costs.

| Source | Fields | Multiplier |
|---|---|---:|
| Gameplay events | `add_stability`, `add_government_power`, `add_legitimacy`, `add_republican_tradition`, `add_devotion`, `add_horde_unity`, `add_tribal_cohesion` | 0.50 |
| Other instantaneous gameplay effects | The same flat effects in Parliament outcomes, laws, interactions, agendas, heir selection, disasters, rebel demands, peace treaties, formables, missions, scripted effects, and on-actions | 0.50 |
| Static gameplay sources | `stability_investment` and the five `monthly_*` government-power modifiers | 0.75 |

Both bonuses and penalties are multiplied toward zero. Parliament debate
modifiers are static sources and therefore use the 0.75 policy. Flat political
effects from Parliament agendas and generic actions use the 0.50 policy.

Honor, Prestige, Religious Influence, and other non-political effects are out
of scope. A vanilla script value shared with any non-political effect is
excluded from central scaling; only its political call sites are transformed.
Consequently no Honor call site is rewritten by this feature.

Instantaneous effects are scanned across gameplay events and all of
`in_game/common`; metadata-only `effect_localization` definitions are excluded.
This means situation/event choices such as plague Stability bonuses or costs
follow the same 0.50 rule even when their implementation delegates to a common
scripted effect.

Static gameplay sources are scanned across all of `in_game/common`, including
advances, estate privileges, government reforms, laws, international
organization rules/statuses, religions, disasters, traits, buildings, and
future vanilla object families that use the same modifier fields.

## Generation contract

Run `tools/generate_all.sh`, or invoke
`tools/generate_political_reward_overrides.py` directly with the vanilla game
root and the Rebalance Economy package root.

The generator:

1. reads gameplay events from vanilla, excluding debug events;
2. writes only affected files at their exact vanilla-relative paths;
3. scales shared political script values once in an exact override of
   `main_menu/common/script_values/default_values.txt`;
4. excludes constants shared with non-political systems from central scaling,
   then generates exact-path overrides for their political uses and for literal
   or dynamic assignments;
5. composes static changes with any exact-path package override already produced
   by US-07, US-09, US-177, or another generator;
6. records whether it created or merely composed each output, so stale cleanup
   never deletes files owned by another feature;
7. records every output and policy in
   `cbp_generated/political_reward_overrides_manifest.json`.

Manifest-owned exact-path files may contain unchanged vanilla
`add_goods_supply` calls. The stock static validator recognizes those files as
generated vanilla carriers rather than CBP-authored stock mutations. When the
vanilla source contains the obsolete `building_upkeep_multiplier` modifier,
the generator removes that line because the package already implements the
confirmed upkeep behavior through `cbp_building_upkeep_auto_modifiers.txt`.

The script-safety validator applies the same exact-path manifest exemption to
unchanged vanilla content inside those carriers. The exemption does not apply
to handwritten CBP files, templates, files absent from the manifest, or the
generator itself.

Vanilla constants used exclusively by political fields are scaled centrally.
Shared constants are left untouched and scaled only at political call sites.
This keeps Honor and other unrelated systems entirely at their vanilla values
while avoiding whole-file overrides for exclusively political constants.

## Validation protocol

1. Run `python3 -m unittest tools.tests.test_political_reward_overrides`.
2. Run `tools/generate_all.sh` twice and confirm the second run produces no diff.
3. Run the repository static validation suite and `git diff --check`.
4. Start a fresh campaign with Rebalance Economy enabled.
5. Trigger one positive and one negative Stability event and verify half of the
   vanilla flat result is applied.
6. Trigger a monarchy government-power event and verify the Legitimacy result is
   halved. Repeat with one non-monarchy government-power type when practical.
7. Resolve one Parliament issue whose pass or failure outcome changes Stability;
   verify the flat outcome is halved and any fixed monthly in-debate modifier is
   75 percent of vanilla.
8. Unlock an advance with a fixed monthly government-power or Stability
   investment modifier and verify it displays 75 percent of vanilla.
9. Review `error.log` for parser, duplicate-key, missing script-value, and event
   namespace errors.
