#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

failures=0

pass() { printf 'PASS  %s\n' "$*"; }
pending() { printf 'PENDING  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*" >&2; failures=$((failures + 1)); }

require_file() {
	local path="$1"
	if [[ -f "$path" ]]; then
		pass "file exists: $path"
	else
		fail "missing file: $path"
	fi
}

require_match() {
	local pattern="$1"
	local path="$2"
	local message="$3"
	if grep -Eq "$pattern" "$path"; then
		pass "$message"
	else
		fail "$message"
	fi
}

printf '%s\n' 'ModeU5 Q8 remaining-candidate probe audit'

probe_effects="packages/modeu5_core_tests/in_game/common/scripted_effects/modeu5_q8_probe_effects.txt"
probe_events="packages/modeu5_core_tests/in_game/events/modeu5_q8_probe_debug_events.txt"
clearance_doc="docs/audits/q8/Q8_2_Q8_4_Q8_5_Q8_6_Q8_7_PROBE_CLEARANCE.md"

require_file "$clearance_doc"
require_file "$probe_effects"
require_file "$probe_events"

require_match '^modeu5_debug_run_q8_remaining_candidate_probes[[:space:]]*=' "$probe_effects" 'aggregate Q8 probe entry point exists'
require_match '^modeu5_q8_probe_debug\.1[[:space:]]*=' "$probe_events" 'Q8 probe event menu exists'

require_match '^modeu5_q8_probe_us10_pending_gate[[:space:]]*=' "$probe_effects" 'Q8.2 runtime probe exists'
require_match 'test_cbp_consumption_wheat_pending_requested_by_market' "$probe_effects" 'Q8.2 probe reads the canonical pending-request map safely'
require_match 'test_cbp_q8_2_us10_pending_gate_probe_passed' "$probe_effects" 'Q8.2 probe reports PASS flag'

require_match '^modeu5_q8_probe_helper_inventory[[:space:]]*=' "$probe_effects" 'Q8.4 runtime/static bridge probe exists'
require_match 'test_cbp_q8_4_helper_inventory_probe_passed' "$probe_effects" 'Q8.4 probe reports PASS flag'

require_match '^modeu5_q8_probe_dirty_cache_lifecycle[[:space:]]*=' "$probe_effects" 'Q8.5 dirty-cache lifecycle probe exists'
require_match 'modeu5_mark_market_country_cache_dirty' "$probe_effects" 'Q8.5 probe marks a market dirty'
require_match 'modeu5_repair_dirty_market_country_caches' "$probe_effects" 'Q8.5 probe repairs dirty market-country cache'

require_match '^modeu5_q8_probe_market_sliced_verifier_candidate[[:space:]]*=' "$probe_effects" 'Q8.6 market-slice candidate probe exists'
require_match 'test_cbp_q8_probe_market_slice_candidates' "$probe_effects" 'Q8.6 probe uses a candidate-market list'

require_match '^modeu5_q8_probe_global_market_iterator_exposure[[:space:]]*=' "$probe_effects" 'Q8.7 global-market exposure probe exists'
require_match 'every_market_in_world' "$probe_effects" 'Q8.7 exposure probe contains the unconfirmed iterator in the test package'
require_match 'test_cbp_q8_7_global_market_probe_passed' "$probe_effects" 'Q8.7 probe reports PASS flag'

pending 'Runtime logs are still required to decide implementation of Q8.2/Q8.4/Q8.5/Q8.6/Q8.7.'

if [[ "$failures" -gt 0 ]]; then
	printf 'ModeU5 Q8 remaining-candidate probe audit failed with %s structural issue(s).\n' "$failures" >&2
	exit 1
fi

printf '%s\n' 'ModeU5 Q8 remaining-candidate probe audit completed: all five probes are present.'
