#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

failures=0

note() { printf '%s\n' "$*"; }
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

search_text() {
	local pattern="$1"
	shift
	if command -v rg >/dev/null 2>&1; then
		rg -n "$pattern" "$@" || true
	else
		grep -REn "$pattern" "$@" || true
	fi
}

note 'ModeU5 Q8 remaining-candidate probe audit'

require_file docs/audits/q8/Q2_systeme_cache.md
require_file docs/audits/q8/Q3_redondances_code.md
require_file docs/audits/q8/Q4_boucles_performance.md
require_file docs/audits/q8/Q5_flux_logique_global.md
require_file docs/audits/q8/Q8_2_Q8_4_Q8_5_Q8_6_Q8_7_PROBE_CLEARANCE.md

# Q8.2 — US-10 aggregate gating.
require_match 'modeu5_pr71_metrics_enabled_trigger' \
	in_game/common/scripted_triggers/modeu5_configuration_triggers.txt \
	'Q8.2 has debug/audit metric surface available from Q8.1'
require_match 'modeu5_consumption_wheat_pending_requested_by_market' \
	in_game/common/scripted_effects/modeu5_zz_pr71_active_good_dispatch_generated.txt \
	'Q8.2 confirms PR7.1 generated US-10 still has per-good pending-request map guard'
pending 'Q8.2 still needs runtime debug/audit evidence before adding a country-market has-any-pending gate.'

# Q8.4 — helper body split.
require_match 'modeu5_process_us00_monthly_market_good_wheat = yes' \
	in_game/common/scripted_effects/modeu5_zz_pr71_active_good_dispatch_generated.txt \
	'Q8.4 sees generated wrapper calling existing US-00 heavy helper'
require_match 'modeu5_process_us10_monthly_market_good_wheat = yes' \
	in_game/common/scripted_effects/modeu5_zz_pr71_active_good_dispatch_generated.txt \
	'Q8.4 sees generated wrapper calling existing US-10 heavy helper'
pending 'Q8.4 requires a full caller inventory before introducing body helpers.'

# Q8.5 — dirty derived-cache surfaces.
require_match '^modeu5_mark_market_country_cache_dirty[[:space:]]*=' \
	in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt \
	'Q8.5 dirty-market writer surface exists'
require_match '^modeu5_repair_dirty_market_country_caches[[:space:]]*=' \
	in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt \
	'Q8.5 dirty-market repair consumer exists'
pending 'Q8.5 should probe producer lifecycle before expanding the cache model.'

# Q8.6 — verifier scope.
world_location_scan_matches="$(search_text 'every_location_in_the_world' in_game packages tools)"
if [[ -n "$world_location_scan_matches" ]]; then
	printf '%s\n' "$world_location_scan_matches" >&2
	fail 'Q8.6 guardrail: no broad every_location_in_the_world verifier should be introduced.'
else
	pass 'Q8.6 guardrail: no broad every_location_in_the_world verifier found in runtime/test/tool files.'
fi
pending 'Q8.6 should start with candidate/dirty market-sliced verifier probes only.'

# Q8.7 — native global market pass exposure.
global_market_live_matches="$(search_text 'every_market_in_world' in_game packages tools)"
if [[ -n "$global_market_live_matches" ]]; then
	printf '%s\n' "$global_market_live_matches" >&2
	fail 'Q8.7 guardrail: every_market_in_world must not be present in live/test code before an exposure probe PR.'
else
	pass 'Q8.7 guardrail: no every_market_in_world usage found in live/test/tool files yet.'
fi
pending 'Q8.7 requires an isolated exposure probe before any dispatcher switch.'

if [[ "$failures" -gt 0 ]]; then
	printf 'ModeU5 Q8 remaining-candidate probe audit failed with %s structural issue(s).\n' "$failures" >&2
	exit 1
fi

printf '%s\n' 'ModeU5 Q8 remaining-candidate probe audit completed: structural checks passed; runtime-only items remain PENDING by design.'
