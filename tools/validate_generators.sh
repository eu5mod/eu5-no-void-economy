#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=tools/modeu5_tool_lib.sh
source "$repo_root/tools/modeu5_tool_lib.sh"

required_templates=(
	"tools/templates/modeu5_stock_good_adapter.template.txt"
	"tools/templates/modeu5_good_transport_helper.template.txt"
	"tools/templates/modeu5_us10_stock_table_row.template.gui"
	"tools/templates/modeu5_us10_market_production_good.template.txt"
	"tools/templates/modeu5_pr71_active_good_dispatch_good.template.txt"
)

for template in "${required_templates[@]}"; do
	modeu5_require_file "$template"
done

required_common_tooling_users=(
	"tools/generate_all.sh"
	"tools/generate_local_runtime_config.sh"
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_good_transport_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
	"tools/generate_pr71_active_good_dispatch_helpers.sh"
)

for script in "${required_common_tooling_users[@]}"; do
	modeu5_require_match 'modeu5_tool_lib\.sh' "$script" "Generator must source the shared ModeU5 tool library"
done

modeu5_require_match 'MODEU5_ENABLE_DEBUG_RUNTIME' \
	"tools/generate_local_runtime_config.sh" \
	'Local runtime config generator must read the explicit ModeU5 debug runtime flag'
modeu5_require_match 'MODEU5_LOCAL_CONFIG_FILE' \
	"tools/generate_local_runtime_config.sh" \
	'Local runtime config generator must allow validation to use an explicit local env file'
modeu5_require_match 'generate_local_runtime_config\.sh' \
	"tools/generate_all.sh" \
	'generate_all must emit the local runtime config before install'
modeu5_require_match 'MODEU5_ENABLE_DEBUG_RUNTIME=false' \
	".modeu5.local.env.template" \
	'Local env template must default ModeU5 debug runtime to false'
modeu5_require_match 'strip_utf8_bom_stream' \
	"tools/generate_us09_economy_overrides.sh" \
	'US-09 generator must strip UTF-8 BOMs from vanilla source streams'
modeu5_require_match 'Generated US-09 files must not contain UTF-8 BOM bytes' \
	"tools/generate_us09_economy_overrides.sh" \
	'US-09 generator must fail if generated output still contains BOM bytes'

local_runtime_tmp_normal="$(mktemp)"
local_runtime_tmp_debug="$(mktemp)"
local_runtime_env_normal="$(mktemp)"
local_runtime_env_debug="$(mktemp)"
pr71_generated_tmp="$(mktemp)"
trap 'rm -f "$local_runtime_tmp_normal" "$local_runtime_tmp_debug" "$local_runtime_env_normal" "$local_runtime_env_debug" "$pr71_generated_tmp"' EXIT

printf '%s\n' 'MODEU5_ENABLE_DEBUG_RUNTIME=false' > "$local_runtime_env_normal"
printf '%s\n' 'MODEU5_ENABLE_DEBUG_RUNTIME=true' > "$local_runtime_env_debug"
bash "$repo_root/tools/generate_local_runtime_config.sh" "$local_runtime_tmp_normal" "$local_runtime_env_normal" >/dev/null
bash "$repo_root/tools/generate_local_runtime_config.sh" "$local_runtime_tmp_debug" "$local_runtime_env_debug" >/dev/null
modeu5_require_match 'modeu5_enter_normal_runtime_mode = yes' \
	"$local_runtime_tmp_normal" \
	'Local runtime config must generate normal runtime when MODEU5_ENABLE_DEBUG_RUNTIME=false'
modeu5_require_match 'modeu5_enter_debug_runtime_mode = yes' \
	"$local_runtime_tmp_debug" \
	'Local runtime config must generate debug runtime when MODEU5_ENABLE_DEBUG_RUNTIME=true'
modeu5_require_match 'modeu5_apply_generated_local_runtime_mode = yes' \
	"in_game/common/scripted_effects/modeu5_configuration_effects.txt" \
	'Configuration initialization must apply the generated local runtime mode'
modeu5_require_match 'ModeU5 debug runtime is now controlled by generated local config / CMM' \
	"in_game/common/scripted_effects/modeu5_configuration_effects.txt" \
	'EU5 engine --debug_mode must not force ModeU5 debug runtime through CMM defaults'

per_good_generators=(
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_good_transport_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
	"tools/generate_pr71_active_good_dispatch_helpers.sh"
)

for script in "${per_good_generators[@]}"; do
	modeu5_require_match 'modeu5_load_goods_registry' "$script" "Per-good generator must load the canonical good registry"
done

if command -v rg >/dev/null 2>&1; then
	literal_good_arrays="$(
		rg -n --glob '*.sh' '^[[:space:]]*(local[[:space:]]+)?[A-Za-z0-9_]*goods[[:space:]]*=\(' tools \
			| grep -Ev 'tools/modeu5_goods\.sh:|goods=\("\$\{modeu5_goods\[@\]\}"\)' || true
	)"
else
	literal_good_arrays="$(
		find tools -name '*.sh' -print0 \
			| xargs -0 grep -En '^[[:space:]]*(local[[:space:]]+)?[A-Za-z0-9_]*goods[[:space:]]*=\(' \
			| grep -Ev 'tools/modeu5_goods\.sh:|goods=\("\$\{modeu5_goods\[@\]\}"\)' || true
	)"
fi

if [[ -n "$literal_good_arrays" ]]; then
	printf '%s\n' 'Generators must not carry local good arrays. Use tools/modeu5_goods.sh as the single good registry.' >&2
	printf '%s\n' "$literal_good_arrays" >&2
	exit 1
fi

pr71_generated_output="in_game/common/scripted_effects/modeu5_zz_pr71_active_good_dispatch_generated.txt"

bash "$repo_root/tools/generate_pr71_active_good_dispatch_helpers.sh" "$pr71_generated_tmp" >/dev/null

if modeu5_search_quiet '__[A-Z_]+__' "$pr71_generated_tmp"; then
	modeu5_search_lines '__[A-Z_]+__' "$pr71_generated_tmp" >&2
	printf '%s\n' 'Generated PR7.1 active-good dispatch output must not contain unresolved template placeholders.' >&2
	exit 1
fi

if [[ -f "$pr71_generated_output" ]] && ! cmp -s "$pr71_generated_output" "$pr71_generated_tmp"; then
	printf '%s\n' 'Generated PR7.1 active-good dispatch file is stale. Run tools/generate_all.sh before validation or install.' >&2
	exit 1
fi

modeu5_require_match 'modeu5_pr71_process_us00_monthly_market_good_wheat' \
	"$pr71_generated_tmp" \
	'PR7.1 generated US-00 guard must contain the canonical wheat helper surface'
modeu5_require_match 'modeu5_pr71_process_us10_monthly_market_good_wheat' \
	"$pr71_generated_tmp" \
	'PR7.1 generated US-10 guard must contain the canonical wheat helper surface'
modeu5_require_match 'modeu5_pr71_metrics_enabled_trigger' \
	"$pr71_generated_tmp" \
	'Q8.1 generated PR7.1 metrics must be gated behind the debug/audit metrics trigger'
modeu5_require_match 'produced_in_market:wheat' \
	"$pr71_generated_tmp" \
	'PR7.1 US-00 guard must preserve the produced-in-market business gate'
modeu5_require_match 'modeu5_probe_us00_previous_record_activity_good_wheat = yes' \
	"$pr71_generated_tmp" \
	'PR7.1 US-00 guard must preserve the previous-record business gate'
modeu5_require_match 'modeu5_consumption_wheat_pending_requested_by_market' \
	"$pr71_generated_tmp" \
	'PR7.1 US-10 guard must preserve the pending-request map gate'
modeu5_require_match 'modeu5_process_us00_monthly_market_good_wheat = yes' \
	"$pr71_generated_tmp" \
	'PR7.1 US-00 guard must call the existing heavy per-good helper only after gating'
modeu5_require_match 'modeu5_process_us10_monthly_market_good_wheat = yes' \
	"$pr71_generated_tmp" \
	'PR7.1 US-10 guard must call the existing heavy per-good helper only after gating'

if modeu5_search_quiet '^modeu5_pr71_prepare_us10_pending_request_gate[[:space:]]*=' "$pr71_generated_tmp"; then
	modeu5_search_lines '^modeu5_pr71_prepare_us10_pending_request_gate[[:space:]]*=' "$pr71_generated_tmp" >&2
	printf '%s\n' 'Q8.2 aggregate US-10 pre-gate must remain deferred and absent from default generated runtime output.' >&2
	exit 1
fi

if modeu5_search_quiet '^modeu5_run_promoted_market_live_local_branch_market_all_goods[[:space:]]*=' "$pr71_generated_tmp"; then
	modeu5_search_lines '^modeu5_run_promoted_market_live_local_branch_market_all_goods[[:space:]]*=' "$pr71_generated_tmp" >&2
	printf '%s\n' 'PR7.1 generator must not emit a duplicate live local-branch effect; EU5 rejects duplicate scripted-effect keys.' >&2
	exit 1
fi

tracked_live_effect="in_game/common/scripted_effects/modeu5_promoted_market_cycle_effects.txt"
modeu5_require_match 'modeu5_prepare_promoted_country_market_capacity' \
	"$tracked_live_effect" \
	'Q4.1 loop merge must preserve per-country capacity refresh in the tracked live handoff'
modeu5_require_match 'modeu5_pr71_prepare_active_good_metrics = yes' \
	"$tracked_live_effect" \
	'Tracked live handoff must prepare PR7.1 active-good metrics'
modeu5_require_match 'modeu5_pr71_process_us00_monthly_market_active_goods = yes' \
	"$tracked_live_effect" \
	'Q4.1 loop merge must run guarded US-00 in the fused capacity/US-00 pass'
modeu5_require_match 'modeu5_pr71_process_us10_monthly_market_pending_goods = yes' \
	"$tracked_live_effect" \
	'PR7.1 tracked live handoff must keep US-10 in the pending-request dispatcher'

tracked_config_triggers="in_game/common/scripted_triggers/modeu5_configuration_triggers.txt"
modeu5_require_match '^modeu5_pr71_metrics_enabled_trigger[[:space:]]*=' \
	"$tracked_config_triggers" \
	'Q8.1 must define the PR7.1 metrics trigger in the configuration trigger surface'
modeu5_require_match '^modeu5_market_sliced_verifier_allowed_trigger[[:space:]]*=' \
	"$tracked_config_triggers" \
	'Q8.6 must define a debug/audit gate for the market-sliced verifier surface'

tracked_capacity_effect="in_game/common/scripted_effects/modeu5_capacity_effects.txt"
modeu5_require_match '^modeu5_calculate_country_storage_capacity_pool_raw[[:space:]]*=' \
	"$tracked_capacity_effect" \
	'Q8.3 must keep a raw country capacity-pool calculator behind the stamped public entry point'
modeu5_require_match '^modeu5_calculate_country_storage_capacity_pool[[:space:]]*=' \
	"$tracked_capacity_effect" \
	'Q8.3 must route the public country capacity-pool helper through the monthly stamp'
modeu5_require_match 'modeu5_capacity_pool_monthly_stamp' \
	"$tracked_capacity_effect" \
	'Q8.3 must stamp the reusable country capacity-pool facts by month'
modeu5_require_match 'modeu5_capacity_pool_cached_location_rank_per_market' \
	"$tracked_capacity_effect" \
	'Q8.3 must cache the reusable country-wide per-market capacity share'

tracked_market_country_cache="in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt"
modeu5_require_match '^modeu5_repair_dirty_market_country_caches_if_needed[[:space:]]*=' \
	"$tracked_market_country_cache" \
	'Q8.5 must expose a guarded dirty market-country cache repair consumer'
modeu5_require_match 'modeu5_market_country_cache_dirty_markets' \
	"$tracked_market_country_cache" \
	'Q8.5 must keep dirty market scheduling in the market-country cache surface'

tracked_market_sliced_verifier="in_game/common/scripted_effects/modeu5_market_sliced_verifier_effects.txt"
modeu5_require_file "$tracked_market_sliced_verifier"
modeu5_require_match '^modeu5_run_market_sliced_verifier_candidates[[:space:]]*=' \
	"$tracked_market_sliced_verifier" \
	'Q8.6 must expose the bounded market-sliced verifier runner'
modeu5_require_match 'modeu5_market_sliced_verifier_candidate_markets' \
	"$tracked_market_sliced_verifier" \
	'Q8.6 must use a bounded candidate market list'
modeu5_require_match 'modeu5_market_sliced_verifier_allowed_trigger' \
	"$tracked_market_sliced_verifier" \
	'Q8.6 verifier must be gated behind debug/audit runtime'
modeu5_require_match 'modeu5_rebuild_countries_present_in_market = yes' \
	"$tracked_market_sliced_verifier" \
	'Q8.6 verifier may rebuild only the current-market country work cache for candidate markets'

printf '%s\n' 'ModeU5 generator and validator convention checks passed'
