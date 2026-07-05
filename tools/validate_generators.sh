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
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_good_transport_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
	"tools/generate_pr71_active_good_dispatch_helpers.sh"
)

for script in "${required_common_tooling_users[@]}"; do
	modeu5_require_match 'modeu5_tool_lib\.sh' "$script" "Generator must source the shared ModeU5 tool library"
done

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

pr71_generated_tmp="$(mktemp)"
trap 'rm -f "$pr71_generated_tmp"' EXIT

bash "$repo_root/tools/generate_pr71_active_good_dispatch_helpers.sh" "$pr71_generated_tmp" >/dev/null

if modeu5_search_quiet '\$[^$]+\$|__[A-Z_]+__' "$pr71_generated_tmp"; then
	modeu5_search_lines '\$[^$]+\$|__[A-Z_]+__' "$pr71_generated_tmp" >&2
	printf '%s\n' 'Generated PR7.1 active-good dispatch output must contain only literal identifiers.' >&2
	exit 1
fi

modeu5_require_match 'modeu5_pr71_process_us00_monthly_market_good_wheat' \
	"$pr71_generated_tmp" \
	'PR7.1 generated US-00 guard must contain the canonical wheat helper surface'
modeu5_require_match 'modeu5_pr71_process_us10_monthly_market_good_wheat' \
	"$pr71_generated_tmp" \
	'PR7.1 generated US-10 guard must contain the canonical wheat helper surface'
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
modeu5_require_match 'modeu5_run_promoted_market_live_local_branch_market_all_goods' \
	"$pr71_generated_tmp" \
	'PR7.1 generated output must expose the guarded live local-branch handoff'
modeu5_require_match 'modeu5_prepare_promoted_country_market_capacity = \{' \
	"$pr71_generated_tmp" \
	'Q4.1 loop merge must preserve per-country capacity refresh in the guarded handoff'
modeu5_require_match 'modeu5_pr71_process_us00_monthly_market_active_goods = yes' \
	"$pr71_generated_tmp" \
	'Q4.1 loop merge must run guarded US-00 in the fused capacity/US-00 pass'
modeu5_require_match 'modeu5_pr71_process_us10_monthly_market_pending_goods = yes' \
	"$pr71_generated_tmp" \
	'PR7.1 guarded handoff must keep US-10 in the pending-request dispatcher'

printf '%s\n' 'ModeU5 generator and validator convention checks passed'
