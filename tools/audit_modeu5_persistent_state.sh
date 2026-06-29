#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tmp_discovered="$(mktemp)"
tmp_expected="$(mktemp)"
tmp_unclassified="$(mktemp)"
trap 'rm -f "$tmp_discovered" "$tmp_expected" "$tmp_unclassified"' EXIT

scan_files=(
	"tools/generate_stock_good_helpers.sh"
	"tools/templates/modeu5_stock_good_adapter.template.txt"
	"in_game/common/scripted_effects/modeu5_capacity_effects.txt"
	"in_game/common/scripted_effects/modeu5_void_economy_effects.txt"
	"in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt"
	"in_game/common/scripted_effects/modeu5_performance_effects.txt"
	"in_game/common/scripted_effects/modeu5_stock_effects.txt"
	"in_game/common/scripted_effects/modeu5_core03_exposure_effects.txt"
)

for file in "${scan_files[@]}"; do
	test -f "$file"
done

{
	for file in "${scan_files[@]}"; do
		LC_ALL=C perl -ne '
			while (/modeu5_\$\{good\}_[a-z0-9_]+/g) {
				my $name = $&;
				$name =~ s/\$\{good\}/<good>/;
				print "$name\n";
			}
			while (/__[A-Z0-9_]+_(?:MAP|LIST)__/g) {
				print "$&\n";
			}
			while (/\bmodeu5_(?:stock_cap|base_capacity|building_capacity|foreign_capacity|void_wealth)_by_market\b/g) {
				print "$&\n";
			}
			while (/\bmodeu5_(?:active_markets_any_good|countries_present_in_market|market_country_cache_dirty_markets|monthly_markets_seen_this_cycle|performance_relevant_markets|core03_probe_seen_locations)\b/g) {
				print "$&\n";
			}
		' "$file"
	done
} | sort -u > "$tmp_discovered"

cat > "$tmp_expected" <<'EOF'
__ACTIVE_LIST__
__ADDED_MAP__
__DIRTY_LIST__
__EFFECTIVE_OVERPRODUCTION_RATIO_MAP__
__MARKET_MAP__
__OVERPRODUCTION_RATIO_MAP__
__PRODUCED_MAP__
__PRODUCTION_PENALTY_MAP__
__REJECTED_MAP__
__STOCK_MAP__
__US00_ACTIVE_MAP__
__UI_MONTHLY_CONSUMPTION_MAP__
__UI_MONTHLY_SURPLUS_MAP__
__VOID_TAXABLE_PROXY_MAP__
__VOID_WEALTH_MAP__
modeu5_<good>_active_markets
modeu5_<good>_added_by_market
modeu5_<good>_dirty_markets
modeu5_<good>_effective_overproduction_ratio_by_market
modeu5_<good>_market_stock
modeu5_<good>_overproduction_ratio_by_market
modeu5_<good>_produced_by_market
modeu5_<good>_production_penalty_by_market
modeu5_<good>_rejected_by_market
modeu5_<good>_stock_by_market
modeu5_<good>_ui_monthly_consumption_by_market
modeu5_<good>_ui_monthly_surplus_by_market
modeu5_<good>_us00_active_record_by_market
modeu5_<good>_void_taxable_income_proxy_by_market
modeu5_<good>_void_wealth_by_market
modeu5_active_markets_any_good
modeu5_base_capacity_by_market
modeu5_building_capacity_by_market
modeu5_core03_probe_seen_locations
modeu5_countries_present_in_market
modeu5_foreign_capacity_by_market
modeu5_market_country_cache_dirty_markets
modeu5_monthly_markets_seen_this_cycle
modeu5_performance_relevant_markets
modeu5_stock_cap_by_market
modeu5_void_wealth_by_market
EOF

comm -23 "$tmp_discovered" <(sort -u "$tmp_expected") > "$tmp_unclassified"

ui_shadow_count="$(
	(
		(grep -E 'modeu5_.*_ui_|__UI_' "$tmp_discovered" || true) |
			grep -Ev 'modeu5_<good>_ui_monthly_(surplus|consumption)_by_market|__UI_MONTHLY_(SURPLUS|CONSUMPTION)_MAP__' || true
	) | wc -l | tr -d ' '
)"

unclassified_count="$(wc -l < "$tmp_unclassified" | tr -d ' ')"

printf '%s\n' 'ModeU5 persistent state audit'
printf '%s\n' 'Stock maps: kept'
printf '%s\n' 'Capacity maps: kept/shared'
printf '%s\n' 'Capacity breakdown maps: kept'
printf '%s\n' 'US-00 gameplay carryover maps: kept'
printf '%s\n' 'US-00 full diagnostic ledger maps: strict/debug/audit or human-relevant only'
printf '%s\n' 'UI monthly counter maps: human country current-month only'
printf 'UI shadow maps: %s\n' "$ui_shadow_count"
printf 'Unclassified persistent maps: %s\n' "$unclassified_count"

if [[ "$ui_shadow_count" != "0" ]]; then
	printf 'Unexpected UI shadow map/list families were found:\n' >&2
	grep -E 'modeu5_.*_ui_|__UI_' "$tmp_discovered" >&2
	exit 1
fi

if [[ "$unclassified_count" != "0" ]]; then
	printf 'Unclassified ModeU5 persistent map/list families were found:\n' >&2
	cat "$tmp_unclassified" >&2
	printf 'Update docs/technical/PERSISTENT_STATE_AUDIT.md and this audit allow-list.\n' >&2
	exit 1
fi
