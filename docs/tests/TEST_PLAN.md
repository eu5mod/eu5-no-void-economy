# TEST PLAN — ModeU5 Country Stocks Within Markets

## Purpose

This file defines how every ModeU5 PR must be tested.

A PR is not complete unless it includes:

```txt
manual test scenario
expected result
actual result
debug output to inspect
error.log result
known limitations
TECH-01 entries updated
```

## Test environments

| Environment | Purpose |
|---|---|
| Clean new game | Check that the mod loads. |
| One-country controlled test | Test stock mutation effects. |
| Multi-country same-market test | Test market stock aggregation and consumption candidate resolution. |
| Multi-market country test | Test country × market split and US-10.2 inter-market transfer. |
| Debug-only event test | Test scripted effects without relying on the full economy cycle. |
| Missing-exposure test | Confirm that fallbacks are logged and do not silently apply gameplay effects. |
| Package-combination test | Confirm that optional packages activate only their documented US set. |

## Required log checks

After every test session, check:

```txt
error.log
game.log
system.log
```

Record:

```txt
No new blocking error
New warnings explained
Known vanilla warning ignored
```

## Package and option tests

### Test P-1 - package publication and source provenance

Setup:

```txt
Run `./tools/validate_module_packages.sh`
Run `./tools/install_local_packages.sh`
Run `./tools/install_local_packages.sh --check`
Refresh the EU5 launcher
```

Expected:

```txt
The source package validation passes
The launcher exposes four distinct ModeU5 entries
Each installed package has the expected unique descriptor name
Each `MODEU5_SOURCE.txt` reports the intended source branch and commit
If two `No Void Economy` entries appear, the older `eu5voideco` single-package entry is disabled
```

---

### Test P0 - default full suite

Setup:

```txt
Enable all four ModeU5 launcher entries in one playset
Start a clean campaign
```

Expected:

```txt
Core, Rebalance Economy, Rebalance Estate Power, and Rebalance Early Blobbing are all loaded
Startup diagnostics report all four matching package versions
No Core script fabricates a package marker for content absent from the playset
```

---

### Test P1 - Core only

Setup:

```txt
Enable No Void Economy only
Start a clean campaign
```

Expected:

```txt
Core stock, void-economy, demand-resolution, decay, and validation systems are available
US-04/05/07/08/09/13 behavior is absent
No optional static override or modifier is present
Startup debug reports Core only
```

---

### Test P2 - Rebalance Economy

Setup:

```txt
Enable Core + Rebalance Economy
Start a clean campaign
```

Expected:

```txt
US-04/05/08/09 and their UI/debug are available
US-07 and US-13 behavior remains absent
Economy package version matches Core
```

---

### Test P3 - Rebalance Estate Power

Setup:

```txt
Enable Core + Rebalance Estate Power
Start a clean campaign
```

Expected:

```txt
US-07 static values and UI are active
US-04/05/08/09 and US-13 behavior remains absent
Core US-02 capacity behavior remains available
Trade package version matches Core
```

---

### Test P4 - Rebalance Early Blobbing

Setup:

```txt
Enable Core + Rebalance Early Blobbing
Start a clean campaign
```

Expected:

```txt
US-13 variants are active
Economy and Trade optional behavior remains absent
War package version matches Core
```

---

### Test P5 - missing or mismatched Core

Setup:

```txt
Load one companion without Core, then with an incompatible Core version
```

Expected:

```txt
Launcher blocks the invalid playset when TECH-01 103 is confirmed
Otherwise startup diagnostics identify the unsupported playset
No optional scripted mutation runs after mismatch detection
```

Adding or removing an optional package from an existing campaign is unsupported until a migration test is explicitly added.

## ModeU5 configuration tests

### Test CFG1 - built-in Game Rules integration

Setup:

```txt
Load Core
Open Game Rules before starting a campaign
Locate ModeU5 Debug Output in the General tab
```

Expected:

```txt
ModeU5 Debug Output offers Off, Basic, and Verbose
Off is the default
No vanilla GUI file is replaced
No custom in-game ModeU5 configuration panel is present
No game-rule parse error is added to error.log
```

---

### Test CFG2 - debug setting initialization

Setup:

```txt
Start three clean campaigns with ModeU5 Debug Output set to Off, Basic, and Verbose
Inspect `modeu5_debug_level` after startup
```

Expected:

```txt
Off initializes `modeu5_debug_level = 0`
Basic initializes `modeu5_debug_level = 1`
Verbose initializes `modeu5_debug_level = 2`
The setting does not mutate stock or package state
```

---

### Test CFG3 - launcher/package boundary

Setup:

```txt
Run clean campaigns with Core only and with each optional companion package
Inspect startup package markers and optional behavior
```

Expected:

```txt
Package presence, not a game rule, controls optional static overrides
No Game Rules setting claims to unload Economy, Trade, or War packages
Adding or removing a package still requires launcher/playset selection before campaign load
No configuration action reseeds or mutates stock
The installed source branch and commit are visible in `MODEU5_SOURCE.txt`
```

---

### Test CFG4 - package lifecycle warning

Setup:

```txt
Open the EU5 mod manager
Hover each ModeU5 entry in the available-mod list
Add each package to a playset and hover the selected entry
```

Expected:

```txt
No Void Economy is identified as required for ModeU5 saves
Every package says it must be selected before campaign start
Together, the descriptions clearly say the package set must remain unchanged for that save
Rebalance Economy identifies its runtime systems and planned static US-08 boundary
Rebalance Estate Power identifies its static US-07 boundary
Rebalance Early Blobbing states that US-13 gameplay is not yet implemented
The warning appears in both available-mod and selected-playset tooltips
No tooltip claims that the launcher technically blocks an unsafe mid-campaign change
```

## Start-game initialization tests

### Test S1 - delayed fresh initialization

Setup:

```txt
Clean new game
No ModeU5 schema marker
No ModeU5 country stock
Two countries with positive capacity in one market
```

Expected:

```txt
Immediate on_game_start does not run world-dependent initialization
ModeU5 dispatcher runs after the documented one-day delay
Capacity is calculated before stock
Initialization state becomes complete
Schema version is persisted
Monthly ModeU5 gameplay remains disabled until completion
```

---

### Test S2 - proportional opening allocation

Setup:

```txt
Market X grain opening source = 200
Country A capacity = 100
Country B capacity = 300
```

Expected:

```txt
Country A initial stock = 50
Country B initial stock = 150
Market aggregate = 200
Difference = 0
Every positive write calls modeu5_add_stock
US-00.1 ledger remains zero
```

---

### Test S3 - opening stock exceeds total capacity

Setup:

```txt
Opening source = 150
Total capacity = 100
```

Expected:

```txt
Country A capacity = 40; initial stock = 60
Country B capacity = 60; initial stock = 90
Allocated stock = 150
Total over-cap quantity = 50
Rejected production = 0
Void wealth = 0
No production penalty is prepared
```

---

### Test S4 - repeated invocation is idempotent

Setup:

```txt
Complete S2
Invoke the startup dispatcher again
```

Expected:

```txt
No stock is added
Country stocks are unchanged
Existing aggregates are validated/rebuilt only if needed
```

---

### Test S5 - unversioned existing source stock

Setup:

```txt
No schema marker
At least one nonzero country stock entry
Market aggregate missing or incorrect
```

Expected:

```txt
Country stock is preserved
No opening allocation occurs
Initialization fails closed
Monthly stock gameplay remains disabled
Explicit migration/recovery is required
```

---

### Test S6 - zero capacity and residue

Setup:

```txt
One market-good has zero total capacity
Another has proportional fixed-point residue above epsilon
```

Expected:

```txt
Positive source with zero total capacity fails initialization without erasing or assigning stock
Residue is assigned only to a country with positive capacity
Residue write calls modeu5_add_stock
Final allocation does not exceed opening target
```

## Country and territory succession tests

### Test L1 - one conquered location

Setup:

```txt
Loser stock = 100
Loser capacity before = 200
Transferred location capacity = 50
```

Expected:

```txt
Transfer ratio = 0.25
Winner receives 25
Loser retains 75
Market aggregate unchanged
No trade economics or demand outcome
```

---

### Test L2 - sequential new-country split

Setup:

```txt
Old stock = 120
Old capacity before = 400
New country receives locations carrying capacity 40 then 60
```

Expected:

```txt
First transfer = 12
Second transfer = 18
New country total = 30
Old country remains 90
Equivalent aggregate ratio = 100 / 400
```

---

### Test L3 - full annexation residual

Setup:

```txt
Country B is annexed by Country A
Location transfers leave a rounding residual of 5 on B
```

Expected:

```txt
Post-annexation finalizer transfers residual 5 to A
B stock key is zero/absent
Market aggregate unchanged
```

---

### Test L3B - succession ignores winner capacity

Setup:

```txt
Loser stock = 100
Loser capacity before = 200
Transferred location capacity = 100
Winner stock before = 90
Winner capacity after = 100
```

Expected:

```txt
Requested and actual transfer = 50
Loser stock after = 50
Winner stock after = 140
Winner over-cap quantity = 40
Target capacity policy = allow_over_capacity
Market aggregate unchanged
No rejected production or unsatisfied demand is recorded
```

---

### Test L4 - lifecycle duplicate prevention

Setup:

```txt
Create/release a country through a path that fires location and country hooks
```

Expected:

```txt
Each location share transfers exactly once
New/released-country finalizer performs validation only
No duplicate stock appears
```

---

### Test L5 - temporary occupation

Setup:

```txt
Occupy a location without changing its owner
```

Expected:

```txt
No CORE-03 stock transfer
Country and market stock remain unchanged
```

## Core invariant tests

### Test 1 — Production simple through `modeu5_add_stock`

Setup:

```txt
Country A stock = 0
Market X stock = 0
Production = 100
Capacity available = 100
```

Expected result:

```txt
Actual added = 100
Rejected quantity = 0
Country A stock = 100
Market X stock = 100
Difference = 0
```

Debug required:

```txt
operation = add_stock
country
market
good
quantity_requested
quantity_actual
quantity_rejected_or_unsatisfied
country_stock_before
country_stock_after
market_stock_before
market_stock_after
stock_difference_after
```

---

### Test 2 — Production with insufficient capacity

Setup:

```txt
Country A stock = 80
Country A cap = 100
Market X stock = 80
Production = 50
```

Expected result:

```txt
Actual added = 20
Rejected = 30
Country A stock = 100
Market X stock = 100
Difference = 0
Rejected quantity is passed to US-00.1
```

---

### Test 2B — Authorized initialization addition above capacity

Setup:

```txt
Country A stock = 0
Country A cap = 40
Market X stock = 0
Initialization allocation = 60
capacity_policy = allow_over_capacity
```

Expected result:

```txt
Actual added = 60
Rejected = 0
Country A stock = 60
Market X stock = 60
Over-cap created = 20
Difference = 0
```

---

### Test 3 — Consumption through `modeu5_remove_stock`

Setup:

```txt
Country A stock = 100
Market X stock = 100
Consumption = 30
```

Expected result:

```txt
Actual removed = 30
Unsatisfied quantity = 0
Country A stock = 70
Market X stock = 70
Difference = 0
```

---

### Test 4 — Consumption above available stock

Setup:

```txt
Country A stock = 30
Market X stock = 30
Consumption = 50
```

Expected result:

```txt
Actual removed = 30
Unsatisfied quantity = 20
Country A stock = 0
Market X stock = 0
Difference = 0
No negative stock persists
```

---

### Test 5 — Same-market transfer does not change market stock

Setup:

```txt
Country A stock in Market X = 100
Country B stock in Market X = 0
Market X stock = 100
Transfer = 40
```

Expected result:

```txt
Country A stock = 60
Country B stock = 40
Market X stock = 100
Difference = 0
No transport cost is calculated
No trade income is created
No trade capacity is consumed
```

---

### Test 6 — Inter-market transfer changes both market stocks

Setup:

```txt
Seller Country A stock in Market X = 100
Buyer Country B stock in Market Y = 0
Buyer Country B capacity in Market Y = 100
Market X stock = 100
Market Y stock = 0
Requested transfer = 40
```

Expected result:

```txt
Transferred quantity = 40
Seller Country A Market X stock = 60
Buyer Country B Market Y stock = 40
Market X stock = 60
Market Y stock = 40
Difference Market X = 0
Difference Market Y = 0
Requested, transferred, and unsatisfied quantities are recorded separately
```

---

### Test 7 — Decay

Setup:

```txt
Country A stock = 100
Country B stock = 100
Market X stock = 200
Decay = 1%
```

Expected result:

```txt
Country A stock = 99
Country B stock = 99
Market X stock = 198
Difference = 0
```

---

### Test 8 — Rebuild safety

Setup:

```txt
Country A stock = 100
Country B stock = 50
Market X stock = 200
```

Expected result after rebuild:

```txt
Market X stock = 150
Difference = 0
Debug inconsistency detected = yes
Country stocks unchanged
No wealth created or destroyed
```

---

### Test 8B — Validation delegates correction to rebuild

Setup:

```txt
Country A stock = 100
Country B stock = 50
Market X stock = 200
Run modeu5_validate_stock_consistency for Market X and the selected good
```

Expected result:

```txt
Expected market stock = 150
Difference before = 50
Inconsistency detected = yes
modeu5_rebuild_market_stock_from_country_stocks called = yes
Market X stock after = 150
Difference after = 0
Second validation performs no write
Country stocks unchanged
```

## US-00 void economy tests

### Test 9 — Location production aggregation

Setup:

```txt
Country A owns locations L1 and L2 in Market X
Country A owns location L3 in Market Y
L1 and L2 produce iron; L2 also produces grain; L3 produces iron
One location contains a foreign-owned productive building
```

Expected:

```txt
Production is read at location × good
L1 and L2 iron aggregate to Country A × Market X × iron
L2 grain remains a separate ledger key
L3 iron aggregates to Country A × Market Y × iron
Debug identifies the exact goods_output/raw_material_output syntax used
Foreign-building ownership behavior is logged and TECH-01 021 is updated
No building/RGO source-level reconstruction is required
```

---

### Test 10 — No overproduction

Setup:

```txt
produced_quantity = 100
actual_added_quantity = 100
rejected_quantity = 0
```

Expected:

```txt
overproduction_ratio = 0
effective_overproduction_ratio = 0
production penalty = 0
void wealth tracked = 0
```

---

### Test 11 — Overproduction below buffer

Setup:

```txt
produced_quantity = 100
actual_added_quantity = 99.5
rejected_quantity = 0.5
target_overproduction_buffer = 0.01
```

Expected:

```txt
overproduction_ratio = 0.005
effective_overproduction_ratio = 0
production penalty = 0
void wealth tracked > 0 if rejected value tracking is enabled
```

Rule:

```txt
The buffer affects the production penalty, not the ledger record of rejected value.
```

---

### Test 12 — Overproduction above buffer

Setup:

```txt
produced_quantity = 100
actual_added_quantity = 70
rejected_quantity = 30
target_overproduction_buffer = 0.01
production_efficiency_penalty_coefficient = 1.00
max_production_efficiency_penalty = 0.25
good_price = 2
void_income_penalty_coefficient = 1.00
```

Expected:

```txt
overproduction_ratio = 0.30
effective_overproduction_ratio = 0.29
production penalty = -0.25
void wealth tracked = 60
```

---

### Test 13 — Multi-market country overproduction

Setup:

```txt
Country A has locations in Market X and Market Y
Iron overproduction in Market X = 30%
Iron overproduction in Market Y = 0%
```

Expected:

```txt
Country A × Market X × Iron penalty > 0
Country A × Market Y × Iron penalty = 0
Country-level void wealth = sum of both markets
No country-wide ratio replaces market-specific values
```

---

### Test 14 — Ledger reset ordering

Setup:

```txt
US-00.1 ledger has produced / added / rejected counters
US-00.2, US-00.3 and US-00.4 have not yet read them
```

Expected:

```txt
No reset occurs before all downstream calculations have read the values
Counters reset only at the end of the monthly cycle
Debug shows reset timing
```

## US-10 demand resolution tests

### Test 15 — Consumption from multiple stock candidates

Setup:

```txt
Demanding Country A requests 100 grain in Market X
Country A stock = 40
Subject Country B stock = 30
Foreign Country C stock = 50
```

Expected:

```txt
ordered_stock_candidates are logged
A stock used first if own_country_bonus is highest
Then B and/or C according to score
satisfied_quantity = 100
unsatisfied_quantity = 0
All removals call modeu5_remove_stock
No trade income or transport cost is generated
```

---

### Test 16 — Consumption with exclusions

Setup:

```txt
Foreign Country C has stock but is at war with buyer
allow_at_war_stocks = no
Foreign Country D has stock but is embargoed
allow_embargoed_stocks = no
```

Expected:

```txt
C excluded with at_war_not_allowed
D excluded with embargoed_stock_not_allowed
Excluded stocks are not used
Debug lists exclusion reason
```

---

### Test 17 — Inter-market transfer limited by buyer capacity

Setup:

```txt
Requested inter-market transfer = 100
Seller stock in source market = 100
Buyer available capacity in target market = 35
```

Expected:

```txt
transferred_quantity = 35
unsatisfied_trade_quantity = 65
source market stock decreases by 35
target market stock increases by 35
transferred_quantity recorded for diagnostics = 35
```

## US-04 demand adaptation tests

### Test 18 — Local demand grows after full-year satisfaction

Setup:

```txt
location_good_months_satisfied_current_year = 12
location_good_months_unsatisfied_current_year = 0
location_good_demand_multiplier = 1.00
annual_satisfied_demand_growth = 0.01
```

Expected:

```txt
location_good_demand_multiplier = 1.01
annual counters reset
```

---

### Test 19 — Local demand decays after full-year shortage

Setup:

```txt
location_good_months_satisfied_current_year = 0
location_good_months_unsatisfied_current_year = 12
location_good_demand_multiplier = 1.00
annual_unsatisfied_demand_decay = 0.01
```

Expected:

```txt
location_good_demand_multiplier = 0.99
annual counters reset
```

---

### Test 20 — Mixed year does not change demand

Setup:

```txt
satisfied months = 8
unsatisfied months = 4
```

Expected:

```txt
location_good_demand_multiplier unchanged
annual counters reset
```

## US-05 Economic Base tests

### Test 21 — Economic Base uses Wealth + Trade Income

Setup:

```txt
wealth = 1000
trade_income = 200
tax_base = 3000
```

Expected:

```txt
modeu5_slider_cost_base = 1200
Tax Base is not used for ModeU5 slider target
Only Stability and Court/Government Power are affected
No gold or modifier reconciliation is applied
Debug identifies the Wealth source and formula call site
```

## Static balance tests

### Test 22 — US-07 trade building overrides

Expected:

```txt
Only confirmed static building fields are changed
Tooltips do not contradict final values
```

### Test 23 — US-08 fixed 50 ducat base price

Expected:

```txt
Relevant RGO/building base price = 50
Dynamic 1.2 price effects are disabled or neutralized only where confirmed
```

### Test 24 — US-09 global Production Efficiency bonus

Expected:

```txt
ModeU5 +5% Production Efficiency compensation is visible
It is not confused with a country-specific or technology bonus
```

## US-13 tests

### Test 25 — Non-horde conquest surcharge by age

Expected:

```txt
Non-horde Age I/II conquest cost uses vanilla + 0.40
Non-horde Age III uses vanilla + 0.20
Age IV+ uses vanilla
Hordes use vanilla
No implementation proceeds until the conquest-cost override is confirmed
```

## PR test report template

Copy this into every PR description:

```md
## Test report

### Scenario

### Files changed

### Expected result

### Actual result

### Debug output inspected

### error.log result

### TECH-01 entries updated

### Known limitations

### Fallbacks used

### MVP boundary check
```
