#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=tools/cbp_tool_lib.sh
source "$repo_root/tools/cbp_tool_lib.sh"
cbp_load_goods_registry

tmp_discovered="$(mktemp)"
tmp_expected_names="$(mktemp)"
tmp_inventory="$(mktemp)"
tmp_unclassified="$(mktemp)"
tmp_direct_writes="$(mktemp)"
tmp_debug_vars="$(mktemp)"
tmp_work_scalars="$(mktemp)"
trap 'rm -f "$tmp_discovered" "$tmp_expected_names" "$tmp_inventory" "$tmp_unclassified" "$tmp_direct_writes" "$tmp_debug_vars" "$tmp_work_scalars"' EXIT

scan_files=(
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
	"tools/templates/cbp_stock_good_adapter.template.txt"
	"in_game/common/scripted_effects/cbp_capacity_effects.txt"
	"in_game/common/scripted_effects/cbp_void_economy_effects.txt"
	"in_game/common/scripted_effects/cbp_market_country_cache_effects.txt"
	"in_game/common/scripted_effects/cbp_market_sliced_verifier_effects.txt"
	"in_game/common/scripted_effects/cbp_performance_effects.txt"
	"in_game/common/scripted_effects/cbp_promoted_market_cycle_effects.txt"
	"in_game/common/scripted_effects/cbp_stock_demand_resolver_effects.txt"
	"in_game/common/scripted_effects/cbp_stock_effects.txt"
	"in_game/common/scripted_effects/cbp_core03_exposure_effects.txt"
	"in_game/common/scripted_effects/cbp_core04_market_entry_effects.txt"
	"in_game/common/scripted_effects/cbp_us10_ui_effects.txt"
)

for file in "${scan_files[@]}"; do
	cbp_require_file "$file"
done

python3 - "$tmp_discovered" "${cbp_goods[*]}" "${scan_files[@]}" <<'PY'
from pathlib import Path
import re
import sys

output = Path(sys.argv[1])
goods = sorted(sys.argv[2].split(), key=len, reverse=True)
files = [Path(p) for p in sys.argv[3:]]

found: set[str] = set()

name_context_patterns = [
    re.compile(r"\bname\s*=\s*([A-Za-z0-9_]+)"),
    re.compile(r"\bvariable\s*=\s*([A-Za-z0-9_]+)"),
    re.compile(r"\bhas_global_variable_list\s*=\s*([A-Za-z0-9_]+)"),
    re.compile(r"\bclear_global_variable_list\s*=\s*([A-Za-z0-9_]+)"),
    re.compile(r"\bclear_variable_list\s*=\s*([A-Za-z0-9_]+)"),
]

free_patterns = [
    re.compile(r"__[A-Z0-9_]+_(?:MAP|LIST)__"),
    re.compile(r"\b(?:cbp|gui_cbp)_\$\{good\}_[A-Za-z0-9_]+(?:_by_market|_markets|_suppliers|_market_stock)\b"),
    re.compile(r"\bcbp_(?:consumption|trade)___GOOD___[A-Za-z0-9_]+_by_market\b"),
]

def normalize_good(name: str) -> str:
    normalized = name.replace("${good}", "<good>").replace("___GOOD___", "_<good>_")
    for good in goods:
        normalized = re.sub(rf"\bcbp_{re.escape(good)}_", "cbp_<good>_", normalized)
        normalized = re.sub(rf"\bgui_cbp_{re.escape(good)}_", "gui_cbp_<good>_", normalized)
        normalized = re.sub(rf"\bcbp_consumption_{re.escape(good)}_", "cbp_consumption_<good>_", normalized)
        normalized = re.sub(rf"\bcbp_trade_{re.escape(good)}_", "cbp_trade_<good>_", normalized)
    return normalized

def is_state_like(name: str) -> bool:
    if name.startswith("__") and name.endswith(("MAP__", "LIST__")):
        return True
    if "_by_market" in name:
        return True
    known_lists = {
        "cbp_active_markets_any_good",
        "cbp_countries_present_in_market",
        "cbp_core03_probe_seen_locations",
        "cbp_detailed_accounting_promoted_markets",
        "cbp_market_country_cache_dirty_markets",
        "cbp_market_sliced_verifier_candidate_markets",
        "cbp_monthly_markets_seen_this_cycle",
        "cbp_performance_relevant_markets",
        "cbp_promoted_markets_this_cycle",
    }
    known_good_lists = {
        "cbp_<good>_active_markets",
        "cbp_<good>_dirty_markets",
        "cbp_<good>_us10_sparse_suppliers",
    }
    return name in known_lists or name in known_good_lists or name == "cbp_<good>_market_stock"

for path in files:
    text = path.read_text(encoding="utf-8")
    for pattern in free_patterns:
        for match in pattern.finditer(text):
            found.add(normalize_good(match.group(0)))
    for pattern in name_context_patterns:
        for match in pattern.finditer(text):
            name = normalize_good(match.group(1))
            if is_state_like(name):
                found.add(name)

output.write_text("\n".join(sorted(found)) + "\n", encoding="utf-8")
PY

cat > "$tmp_inventory" <<'EOF'
name	kind	class	owner	rebuild_or_write_trigger	reset_policy	lifecycle
__ACTIVE_LIST__	template list placeholder	work cache	global	mark active market / active-list repair	clear during active-list rebuild	generated per-good active-market list
__ADDED_MAP__	template map placeholder	monthly ledger	country	US-00 production rejection ledger update	monthly after readers	current month until readers reset
__DIRTY_LIST__	template list placeholder	work cache	global	central stock mutation marks dirty	clear after reconciliation/explicit reset	dirty until reconciliation/clear
__EFFECTIVE_OVERPRODUCTION_RATIO_MAP__	template map placeholder	derived monthly ledger	country	US-00 ratio finalization from frozen facts	monthly after readers	current month until readers reset
__MARKET_MAP__	template map placeholder	derived cache	global	central stock operators or rebuild from country stock	never clear as source; rebuild from country stock	rebuilt/updated from country stock
__OVERPRODUCTION_RATIO_MAP__	template map placeholder	derived monthly ledger	country	US-00 ratio calculation from frozen facts	monthly after readers	current month until readers reset
__PRODUCED_MAP__	template map placeholder	monthly ledger	country	US-00 production ingestion	monthly after readers	current month until readers reset
__PRODUCTION_PENALTY_MAP__	template map placeholder	gameplay carryover	country	US-00 next-month penalty finalization	replace when next penalty is finalized	next-month carryover
__REJECTED_MAP__	template map placeholder	monthly ledger	country	US-00 stock admission result	monthly after readers	current month until readers reset
__SPARSE_SUPPLIER_LIST__	template list placeholder	work cache	global	US-10 sparse supplier preparation	clear before each market/good rebuild	rebuilt per US-10 market/good scan
__STOCK_MAP__	template map placeholder	source	country	central stock operators only	never clear except explicit migration/test	durable authoritative stock
__US00_ACTIVE_MAP__	template map placeholder	work cache	country	PERF-15 active-record probe/update	rebuild or remove when record becomes inactive	PERF-15 scheduling index
__UI_MONTHLY_CONSUMPTION_MAP__	template map placeholder	UI monthly counter	human country	US-10/UI current-month capture	monthly after UI/readers	current month only
__UI_MONTHLY_SURPLUS_MAP__	template map placeholder	UI monthly counter	human country	US-00/UI current-month capture	monthly after UI/readers	current month only
__VOID_TAXABLE_PROXY_MAP__	template map placeholder	diagnostic ledger	country	US-00 void wealth proxy finalization	strict/debug/audit or monthly after readers	strict/debug/audit or human-relevant only
__VOID_WEALTH_MAP__	template map placeholder	diagnostic ledger	country	US-00 void wealth finalization	strict/debug/audit or monthly after readers	strict/debug/audit or human-relevant only
cbp_<good>_active_markets	global list	work cache	global	mark active market / active-list repair	clear during active-list rebuild	additive until rebuild/repair
cbp_<good>_added_by_market	variable map	monthly ledger	country	US-00 production rejection ledger update	monthly after readers	current month until readers reset
cbp_<good>_dirty_markets	global list	work cache	global	central stock mutation marks dirty	clear after reconciliation/explicit reset	dirty until reconciliation/clear
cbp_<good>_effective_overproduction_ratio_by_market	variable map	derived monthly ledger	country	US-00 ratio finalization from frozen facts	monthly after readers	current month until readers reset
cbp_<good>_market_stock	global variable map	derived cache	global	central stock operators or rebuild from country stock	never clear as source; rebuild from country stock	rebuilt from country stock
cbp_<good>_overproduction_ratio_by_market	variable map	derived monthly ledger	country	US-00 ratio calculation from frozen facts	monthly after readers	current month until readers reset
cbp_<good>_produced_by_market	variable map	monthly ledger	country	US-00 production ingestion	monthly after readers	current month until readers reset
cbp_<good>_production_penalty_by_market	variable map	gameplay carryover	country	US-00 next-month penalty finalization	replace when next penalty is finalized	next-month carryover
cbp_<good>_rejected_by_market	variable map	monthly ledger	country	US-00 stock admission result	monthly after readers	current month until readers reset
cbp_<good>_stock_by_market	variable map	source	country	central stock operators only	never clear except explicit migration/test	durable authoritative stock
gui_cbp_<good>_ui_monthly_consumption_by_market	variable map	UI monthly counter	human country	US-10/UI current-month capture	monthly after UI/readers	current month only
gui_cbp_<good>_ui_monthly_surplus_by_market	variable map	UI monthly counter	human country	US-00/UI current-month capture	monthly after UI/readers	current month only
cbp_<good>_us00_active_record_by_market	variable map	work cache	country	PERF-15 active-record probe/update	rebuild or remove when record becomes inactive	PERF-15 previous-state scheduling
cbp_<good>_us10_sparse_suppliers	global list	work cache	global	US-10 sparse supplier preparation	clear before each market/good rebuild	rebuilt per US-10 market/good scan
cbp_<good>_void_taxable_income_proxy_by_market	variable map	diagnostic ledger	country	US-00 void wealth proxy finalization	strict/debug/audit or monthly after readers	strict/debug/audit or human-relevant only
cbp_<good>_void_wealth_by_market	variable map	diagnostic ledger	country	US-00 void wealth finalization	strict/debug/audit or monthly after readers	strict/debug/audit or human-relevant only
cbp_active_markets_any_good	global list	work cache	global	mark active market / active-list repair	clear during active-list rebuild	additive until rebuild/repair
cbp_base_capacity_by_market	variable map	capacity breakdown	country	capacity refresh / init / owner-rank-capital hooks	replace during capacity refresh	with capacity refresh
cbp_building_capacity_by_market	variable map	capacity breakdown	country	capacity refresh / init / owner-rank-capital hooks	replace during capacity refresh	with capacity refresh
cbp_consumption_<good>_pending_requested_by_market	variable map	monthly input queue	country	explicit US-10 request enqueue	remove when processed by monthly pass	removed when US-10 monthly pass consumes it
cbp_consumption_<good>_requested_by_market	variable map	monthly ledger	country	US-10 same-market consumption resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_consumption_<good>_satisfied_by_market	variable map	monthly ledger	country	US-10 same-market consumption resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_consumption_<good>_unsatisfied_by_market	variable map	monthly ledger	country	US-10 same-market consumption resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_core03_probe_seen_locations	global list	debug-only	global	CORE-03 explicit debug probe	clear before probe	explicit CORE-03 probe only
cbp_countries_present_in_market	global list	work cache	global	cbp_rebuild_countries_present_in_market	clear before each target/promoted-market rebuild	rebuilt per target/promoted market
cbp_detailed_accounting_promoted_markets	global list	work cache	global	PERF-14 successful promotion	clear on explicit promoted-market rebuild/reset	rebuilt/marked by PERF-14 promotion
cbp_foreign_capacity_by_market	variable map	capacity breakdown	country	capacity refresh / init / owner-rank-capital hooks	replace during capacity refresh	with capacity refresh
cbp_market_country_cache_dirty_markets	global list	work cache	global	ownership/cache repair marks affected markets	clear during cache repair	dirty until repair
cbp_market_sliced_verifier_candidate_markets	global list	work cache	global	Q8.6 verifier candidate preparation	clear before each verifier run	debug/audit candidate-market verifier slice
cbp_monthly_markets_seen_this_cycle	global list	work cache	global	monthly seen-market preparation	reset once per month	reset once per month
cbp_performance_relevant_markets	global list	work cache	global	human/performance relevance rebuild	clear before relevance rebuild	rare/explicit rebuild
cbp_promoted_markets_this_cycle	global list	work cache	global	PR126 promoted-market dispatcher shell preparation	clear before each promoted-market shell preparation	test-only shell work list until dispatcher is wired
cbp_stock_cap_by_market	variable map	capacity source	country	capacity refresh / init / owner-rank-capital hooks	replace during capacity refresh	init/hooks/monthly capacity refresh
cbp_trade_<good>_requested_by_market	variable map	monthly ledger	country	US-10 inter-market transfer resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_trade_<good>_transferred_by_market	variable map	monthly ledger	country	US-10 inter-market transfer resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_trade_<good>_unsatisfied_by_market	variable map	monthly ledger	country	US-10 inter-market transfer resolution	monthly after US-10.3/UI readers	current month until readers reset
cbp_void_wealth_by_market	variable map	diagnostic ledger	country	US-00 all-goods void wealth aggregation	strict/debug/audit or monthly after readers	strict/debug/audit or explicit UI only
EOF

cut -f1 "$tmp_inventory" | tail -n +2 | sort -u > "$tmp_expected_names"
comm -23 "$tmp_discovered" "$tmp_expected_names" > "$tmp_unclassified"

python3 - "$tmp_direct_writes" <<'PY'
from pathlib import Path
import re
import sys

roots = [Path("in_game"), Path("packages"), Path("tools/templates")]
excluded = {
    Path("in_game/common/scripted_effects/cbp_stock_goods_generated.txt"),
    Path("in_game/common/scripted_effects/cbp_transport_cost_generated.txt"),
}
allowed_stock_write_files = {
    Path("tools/templates/cbp_stock_good_adapter.template.txt"),
}

block_start = re.compile(r"\b(?:add_to_variable_map|remove_from_variable_map)\s*=\s*\{")
stock_name = re.compile(r"\bname\s*=\s*(?:__STOCK_MAP__|cbp_[A-Za-z0-9_]+_stock_by_market)\b")
findings: list[str] = []

for root in roots:
    if not root.exists():
        continue
    for path in sorted(root.rglob("*.txt")):
        if path in excluded:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not block_start.search(line):
                continue
            window = "\n".join(lines[index:index + 10])
            if not stock_name.search(window):
                continue
            if path in allowed_stock_write_files:
                continue
            findings.append(f"{path}:{index + 1}: {line.strip()}")

Path(sys.argv[1]).write_text("\n".join(findings) + ("\n" if findings else ""), encoding="utf-8")
PY

python3 - "$tmp_debug_vars" "$tmp_work_scalars" "${scan_files[@]}" <<'PY'
from pathlib import Path
import re
import sys

debug_out = Path(sys.argv[1])
work_out = Path(sys.argv[2])
files = [Path(p) for p in sys.argv[3:]]

debug_names: set[str] = set()
work_names: set[str] = set()
debug_pattern = re.compile(r"\bcbp_debug(?:_last)?_[A-Za-z0-9_]+\b")
work_pattern = re.compile(
    r"\bcbp_(?:perf\d+|performance|human_relevant|monthly|reconciliation|active_repair|us10_ui)_[A-Za-z0-9_]+\b"
)

for path in files:
    text = path.read_text(encoding="utf-8")
    debug_names.update(debug_pattern.findall(text))
    work_names.update(work_pattern.findall(text))

debug_out.write_text("\n".join(sorted(debug_names)) + ("\n" if debug_names else ""), encoding="utf-8")
work_out.write_text("\n".join(sorted(work_names)) + ("\n" if work_names else ""), encoding="utf-8")
PY

ui_shadow_count="$(
	(
		(grep -E 'cbp_.*_ui_|__UI_' "$tmp_discovered" || true) |
			grep -Ev 'cbp_<good>_ui_monthly_(surplus|consumption)_by_market|__UI_MONTHLY_(SURPLUS|CONSUMPTION)_MAP__' || true
	) | wc -l | tr -d ' '
)"

unclassified_count="$(wc -l < "$tmp_unclassified" | tr -d ' ')"
direct_write_count="$(wc -l < "$tmp_direct_writes" | tr -d ' ')"
policy_gap_count="$(
	awk -F '\t' 'NR > 1 && (NF < 7 || $4 == "" || $5 == "" || $6 == "") { count++ } END { print count + 0 }' "$tmp_inventory"
)"
source_count="$(awk -F '\t' 'NR > 1 && $3 == "source" { count++ } END { print count + 0 }' "$tmp_inventory")"
derived_count="$(awk -F '\t' 'NR > 1 && $3 ~ /derived|capacity breakdown|diagnostic/ { count++ } END { print count + 0 }' "$tmp_inventory")"
work_count="$(awk -F '\t' 'NR > 1 && $3 ~ /work cache/ { count++ } END { print count + 0 }' "$tmp_inventory")"
monthly_count="$(awk -F '\t' 'NR > 1 && $3 ~ /monthly|carryover|input queue/ { count++ } END { print count + 0 }' "$tmp_inventory")"
debug_count="$(wc -l < "$tmp_debug_vars" | tr -d ' ')"
work_scalar_count="$(wc -l < "$tmp_work_scalars" | tr -d ' ')"

printf '%s\n' 'ModeU5 persistent state audit'
printf 'Source state families: %s\n' "$source_count"
printf 'Derived/cache/diagnostic families: %s\n' "$derived_count"
printf 'Work-cache/list families: %s\n' "$work_count"
printf 'Monthly/carryover ledger families: %s\n' "$monthly_count"
printf 'Debug scalar variables discovered: %s\n' "$debug_count"
printf 'Work/metric scalar variables discovered: %s\n' "$work_scalar_count"
printf '%s\n' 'Stock maps: kept'
printf '%s\n' 'Capacity maps: kept/shared'
printf '%s\n' 'Capacity breakdown maps: kept'
printf '%s\n' 'US-00 gameplay carryover maps: kept'
printf '%s\n' 'US-00 full diagnostic ledger maps: strict/debug/audit or human-relevant only'
printf '%s\n' 'US-10 monthly demand ledgers: current-month until readers reset'
printf '%s\n' 'Work caches: scheduling only, never stock source'
printf '%s\n' 'Debug variables: diagnostic only, never business source'
printf '%s\n' 'UI monthly counter maps: human country current-month only'
printf 'UI shadow maps: %s\n' "$ui_shadow_count"
printf 'Unclassified persistent maps/lists: %s\n' "$unclassified_count"
printf 'Direct stock-map write candidates outside generated adapter template: %s\n' "$direct_write_count"
printf 'Ownership/rebuild/reset policy gaps: %s\n' "$policy_gap_count"

if [[ "$ui_shadow_count" != "0" ]]; then
	printf 'Unexpected UI shadow map/list families were found:\n' >&2
	grep -E 'cbp_.*_ui_|__UI_' "$tmp_discovered" >&2
	exit 1
fi

if [[ "$unclassified_count" != "0" ]]; then
	printf 'Unclassified ModeU5 persistent map/list families were found:\n' >&2
	cat "$tmp_unclassified" >&2
	printf 'Update docs/technical/PERSISTENT_STATE_AUDIT.md and this audit inventory.\n' >&2
	exit 1
fi

if [[ "$direct_write_count" != "0" ]]; then
	printf 'Suspicious direct stock-map writes were found outside the generated adapter template:\n' >&2
	cat "$tmp_direct_writes" >&2
	printf 'Stock mutation must go through centralized operators and generated adapters.\n' >&2
	exit 1
fi

if [[ "$policy_gap_count" != "0" ]]; then
	printf 'Persistent state inventory entries missing owner/rebuild/reset policy:\n' >&2
	awk -F '\t' 'NR > 1 && (NF < 7 || $4 == "" || $5 == "" || $6 == "") { print }' "$tmp_inventory" >&2
	exit 1
fi
