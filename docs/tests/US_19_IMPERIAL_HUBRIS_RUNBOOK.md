# US-19 Imperial Hubris / Imperial Complacency Runbook

## Purpose

Validate the optional Early Blobbing balance story that tracks Imperial
Complacency for Great Powers.

The important performance contract is that the monthly country pulse reads
`modeu5_has_great_power_war`; it must not run a broad country/war scan. War
lifecycle hooks update the cached variable when wars start, end, or a country
joins/loses a war.

## Packages

Enable before starting the campaign:

```txt
No Void Economy
Rebalance Early Blobbing
```

Do not add or remove packages mid-save.

## Static Checks

Run from the repository root:

```sh
./tools/validate_module_packages.sh
git diff --check
```

## Scenario A — Deterministic State-Machine Probe

1. Install the current branch.
2. Start or load a disposable campaign with the Early Blobbing package enabled.
3. Open the console.
4. Run:

```txt
event modeu5_us19_debug.1
```

5. Choose:

```txt
Run US-19 imperial complacency probe
```

Expected `debug.log` lines:

```txt
ModeU5 TEST ENTERED scenario=us19_imperial_complacency
ModeU5 US-19 DUMP state_machine complacency_after=<value below 150> gp_war_state=1
ModeU5 TEST PASS scenario=us19_imperial_complacency
```

Expected result:

```txt
PASS
```

If the result is `FAIL`, inspect `error.log` for the US-19 failure line and
check whether the static modifier loaded.

## Scenario B — Real War-State Hook Probe

This scenario validates the event-driven tracker. It is intentionally manual
because it depends on the diplomatic situation in the current campaign.

1. Start as a Great Power or switch to one of the top-8 Great Powers.
2. Record the initial value of:

```txt
modeu5_has_great_power_war
```

3. Start or join a war against another Great Power.
4. Wait at least one daily tick.
5. Confirm that the country variable is now:

```txt
modeu5_has_great_power_war = 1
```

6. End the war or make peace.
7. Wait at least one daily tick.
8. Confirm that the variable returns to `0` if no other Great Power war remains.

Expected result:

```txt
The tracker changes only around war lifecycle events, not through a monthly scan.
```

## Scenario C — Monthly Modifier Smoke Test

1. Use a Great Power with positive `modeu5_imperial_complacency`.
2. Let a monthly tick pass.
3. Inspect whether the country receives:

```txt
modeu5_imperial_complacency
```

Expected result:

```txt
The modifier appears only when the country remains a Great Power and the
complacency variable is positive.
```

## Logs To Review

```txt
error.log
game.log
debug.log
system.log
```

`debug.log` is the source of truth for deterministic test output. `error.log`
must not contain new blocking ModeU5 script errors.

## Known Limitations

- Scenario A validates the state machine and dump output, not real diplomacy.
- Scenario B validates real hooks but depends on campaign politics.
- Modifier sign and balance scale are intentionally conservative and should be
  reviewed after one in-game runtime validation pass.
- The package is optional and pre-campaign only.
