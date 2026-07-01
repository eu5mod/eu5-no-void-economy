# CORE-04 — Market topology stock persistence

Labels: `module:core`, `stock-persistence`, `performance-mode`

## Purpose

Define how ModeU5 preserves stock when market topology changes, without adding
location-level stock persistence.

This PR is stacked on PERF-14 / PR #120. It covers the missing persistence class
that is separate from CORE-03 ownership succession:

- market creation or replacement;
- market removal or merge;
- a location moving from one market to another while keeping the same owner;
- a country entering a newly human-relevant market in Performance Mode.

## Non-goal: no location-level stock

Do not persist stock at location level.

ModeU5 stock should remain stored as:

```txt
country x market x good
market x good aggregate/cache
```

Location or topology events may provide the capacity numerator, but they must not
become a new stock storage dimension.

## Business rule: first market entry only

A same-country market-topology change only moves stock when the target market is
new for that country.

This models the two meaningful “country enters a market” cases:

- a country becomes present in a market because market attractiveness or access
  changes;
- a new market is created and the country receives its first presence there.

If the country has already been present in both markets, later oscillation of
locations between those known markets does **not** move stock. Only capacities,
market-country caches, and validation state are refreshed. The country keeps the
stocks already persisted in each market.

Role-play interpretation: the country is rebalancing locations between already
exploited markets; it may leave warehouses, inventories, and commercial stock in
the market where they already existed instead of physically moving them every
time a location changes market preference.

This avoids noisy stock churn for cases such as:

```txt
Spanish location switches from Barcelona market to Seville market
Spanish country already has known stock/capacity history in both markets
=> no stock migration; refresh capacity/cache only
```

## Shared rule for first entry

When the target market is new for the country, reuse the CORE-03 principle:

```txt
stock portion moved = storage portion moved
```

For one country, one good, and one first-entry market-topology transition:

```txt
source_stock_before = S
source_capacity_before = C
moved_storage_capacity = D

if C > 0:
  move_ratio = clamp(D / C, 0, 1)
else:
  move_ratio = 0

requested_stock_move = S * move_ratio
```

The resulting stock movement is:

```txt
same country x old market x good
  -> same country x new market x good
```

This is not trade and must not create trade income, transport cost, or demand
records.

If the target market is already known for the country, the requested stock move
is forced to zero even if a location moved between markets.

## Relationship with existing systems

CORE-03 already handles owner changes:

```txt
old owner x market x good -> new owner x same market x good
```

CORE-04 handles first-time market entry for the same owner:

```txt
same owner x old market x good -> same owner x new market x good
```

Both use storage share when stock movement is required. Neither requires
location-level stock.

Known-market oscillation is deliberately different from CORE-03: ownership did
not change and the target market is not new, so stock remains where it was.

## Implementation guidance

Do not duplicate capacity or allocation formulas. Reuse existing helpers wherever
possible:

```txt
modeu5_rebuild_countries_present_in_market
modeu5_rebuild_and_refresh_country_storage_capacities
modeu5_recalculate_saved_country_storage_capacities
modeu5_recalculate_country_market_capacity_shared
modeu5_calculate_location_storage_capacity
modeu5_transfer_stock
modeu5_validate_stock_consistency
```

If CORE-02 opening allocation is too coupled to start-game initialization, split
out a reusable lower-level capacity-share allocation helper and make both
CORE-02 and Performance Mode promotion call it.

Suggested helper contracts:

```txt
modeu5_country_market_known_trigger = {
  country = <country>
  market = <market>
  # true if the country has ever had persisted presence in this market
}

modeu5_mark_country_market_known = {
  country = <country>
  market = <market>
}

modeu5_promote_market_to_detailed_accounting = {
  market = <market>
  # aggregate -> country-record materialization, idempotent
}

modeu5_move_country_market_stock_by_storage_share = {
  country = <country>
  source_market = <old market>
  target_market = <new market>
  moved_storage_capacity = <capacity contribution>
  # no-op unless target market is new for the country
}
```

All stock writes must still go through centralized CORE-01 operators.

## Required behavior

### Location moves market

When old and new market scopes are known:

1. check whether the owner country already knows the target market;
2. if the target market is new for the country:
   - read the owner country stock and capacity in the old market before capacity
     refresh;
   - compute moved storage capacity using the same US-02 location-capacity helper
     used by CORE-03;
   - move the proportional stock share from old market to new market for every
     good;
   - mark the target market as known for that country;
3. if the target market is already known for the country:
   - do not move stock;
   - preserve existing stock in both market records;
4. refresh capacities for both affected markets;
5. mark affected market-country caches dirty;
6. validate both affected market-good aggregates.

### Market creation or replacement

If a new market receives a country for the first time, process a first-entry
stock settlement using the storage-share rule.

If the country was already known in the target market, do not move stock merely
because a location oscillated back into that market. Refresh capacity/cache only.

The new market receives stock only through confirmed topology transition data or
an explicitly approved fallback.

### Market removal or merge

If a market has a known successor and the old market key will become unusable,
this is not a normal oscillation case. Migrate stock out of the old market before
old keys are cleared.

If no successor is known, do not silently remove stock; log a blocking CORE-04
diagnostic and keep the behavior disabled until a safe fallback is approved.

### Performance Mode promotion

When a market becomes human-relevant and detailed stock mutation is required,
use the PERF-14 promotion initializer. It must:

- rebuild countries present in the market;
- refresh country x market capacities;
- split aggregate-only market stock into country records by capacity share;
- preserve the market aggregate exactly;
- be idempotent;
- mark affected market-good records dirty or validation-required.

Performance Mode promotion is a materialization step for aggregate-only stock,
not a location-level stock migration. It should use the same capacity-share
allocation policy, but it should not create a separate location stock store.

## Persistence invariants

After every stock-affecting market-topology operation:

```txt
sum(country x market stock for good) == market aggregate stock for good
```

Additional invariants:

- no location-level stock is persisted;
- same-country market movement is not trade;
- same-country movement into an already-known market does not move stock;
- first entry into a new market may move the storage-share stock portion;
- no stock is dropped because a market became inactive or no longer detailed;
- running promotion or migration twice must not duplicate stock;
- obsolete market keys are cleared only after their stock is moved or validated
  as zero.

## Test scenarios

1. **Performance Mode aggregate promotion**: market aggregate stock exists, no
   country records exist, promotion creates country records by capacity share and
   preserves the aggregate.
2. **Idempotent promotion**: running promotion twice does not duplicate stock.
3. **Partial-state promotion**: some country records already exist; promotion
   allocates only the missing/residual quantity.
4. **First entry into new market**: country has stock/capacity in old market,
   target market is unknown for that country, location enters target market, and
   stock moves by moved storage-capacity share.
5. **Known-market oscillation**: country has known history in both old and target
   markets, a location moves between them, and no stock moves; only capacities,
   caches, and validation state update.
6. **Market creation/replacement**: new market receives stock only when it is a
   first-entry market for that country or when an approved successor migration
   requires it.
7. **Unknown successor**: no guessed deletion; emit diagnostic and keep stock
   unchanged.

## Acceptance criteria

- No location-level stock storage is introduced.
- Stock migration uses `stock portion = storage portion` only for first entry or
  explicit successor migration.
- Known-market oscillation preserves existing stock in each market.
- Market creation, removal, and reassignment have explicit contracts.
- Existing US-02/CORE-01/CORE-02 helpers are reused instead of duplicating
  capacity or allocation logic.
- Market aggregates remain equal to country stock sums after every migration.
- Any missing old/new market engine exposure is treated as a blocker, not as a
  guessed stock migration.

## Open exposure questions

- Is there a confirmed hook for a location changing market with old and new
  market scopes?
- Does market creation expose the old source market for moved locations?
- Does market removal expose a successor market before the old key becomes
  unusable?
- Can ModeU5 safely identify old market keys after a market disappears?
- What is the safest persistent representation for “country has ever been known
  in this market” without adding high-cardinality stock records?
