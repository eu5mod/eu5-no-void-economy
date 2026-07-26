# Once-Per-Month Global Market Owner

## Decision

Monthly market-local accounting has one live traversal:

```text
first eligible monthly country pulse
  -> cbp_run_monthly_q8_7_global_market_local_cycle_once
     -> every_market_in_world
        -> shared per-market accounting

later monthly country pulses
  -> bypass every_market_in_world through the global month stamp
  -> continue current-country trade and US-04 work
```

The former rollback traversal is retired from live code:

```text
current country
  -> every_market_center_in_country
  -> shared per-market accounting
```

This change is implemented directly on PR #215 head
`d17222246824892e0b3d356f0287f6e1e256da2e`. It does not reuse or merge the
history of PR #216.

## Removed runtime surfaces

- `cbp_q8_7_live_global_market_owner_disabled`;
- `cbp_enable_q8_7_live_global_market_owner`;
- `cbp_disable_q8_7_live_global_market_owner`;
- `cbp_q8_7_live_global_market_owner_enabled_trigger`;
- `cbp_q8_7_live_global_market_owner_disabled_trigger`;
- the owner-selection conditional in
  `cbp_run_monthly_stock_cycle_q8_7_owner_switch`;
- the live call to `cbp_run_monthly_promoted_market_local_cycle`;
- `in_game/common/scripted_triggers/cbp_q8_7_global_owner_triggers.txt`.

The historical wrapper name
`cbp_run_monthly_stock_cycle_q8_7_owner_switch` remains as a stable entry point,
but it no longer selects an owner.

## Preserved boundaries

The change preserves:

- the global once-per-month stamp;
- exactly one `every_market_in_world` iterator;
- detailed, Vanilla-fallback, and blocked per-market accounting modes;
- the US-00-before-US-10 two-pass invariant;
- country-owned `every_trade` processing;
- PR #215 sparse US-04 scheduling and reconciliation;
- PR #215 observability gating for Q8.7 counters;
- audit reconciliation and CORE-04 location-market memory.

The required execution order remains:

```text
global market pass
  -> country trade owner
  -> monthly US-04 owner
```

## Static contract

`tools/validate_cbp_global_market_owner_only.py` rejects:

- restoration of the trigger file or disable-variable contract;
- restoration of the market-center branch in live owner code;
- multiple or missing `every_market_in_world` iterators;
- loss of the global month stamp;
- loss of any per-market accounting mode;
- loss of Q8.7 observability guards;
- reordering of global markets, country trades, and monthly US-04;
- reintroduction of the retired path in the normative Mermaid diagram.
