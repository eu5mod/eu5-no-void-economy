# Trade Rework Gate Correction

## Decision

The CMM option `cbp_general_gameplay_gameplay_trade_rework_settings` owns both
US-17 and US-20, including the country-scoped native `every_trade` traversal that
feeds them.

## Correct runtime contract

```txt
option enabled
  -> refresh US-17 country modifier state
  -> every_trade
     -> capture owner, source, target, good, and trade_volume
     -> run US-17 route compatibility surface
     -> run US-20 route-loss and goods reconciliation

option disabled
  -> clear persisted US-17 correction/baseline state
  -> remove the persisted US-20 route-loss coefficient
  -> do not enter every_trade
```

The explicit ModeU5 inter-market request handler is not a native trade-rework
surface and remains callable independently.

## Why the previous flow was misleading

The previous implementation had three different levels of gating:

1. `cbp_refresh_us17_native_profit_modifiers_for_current_country` checked the CMM
   option internally and cleared its state when disabled.
2. The US-17 route compatibility wrapper was called for every native trade but
   returned a zero treasury delta.
3. US-20 had an additional inner CMM gate.

Consequently, disabling the option prevented the effective US-17 modifier and
US-20 goods mutation, but still executed the outer refresh call, the complete
`every_trade` traversal, trade scope capture, and the zero-delta US-17 wrapper.

The corrected owner-level gate removes that ambiguity and avoids all native
trade-route work when the option is disabled.

## Static protection

The contract is enforced by:

- `tools/validate_cbp_trade_rework_gate.py`;
- the US-17/US-20 checks in `tools/validate_ci_static_contracts.py`;
- the `Observability Gates` workflow.

The validators require one authoritative gate and the order:

```txt
gate -> refresh -> every_trade -> US-17 -> US-20
```

They also require a disabled branch that clears persisted country state.
