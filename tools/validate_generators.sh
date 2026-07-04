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
)

for template in "${required_templates[@]}"; do
	modeu5_require_file "$template"
done

required_common_tooling_users=(
	"tools/generate_all.sh"
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_good_transport_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
)

for script in "${required_common_tooling_users[@]}"; do
	modeu5_require_match 'modeu5_tool_lib\.sh' "$script" "Generator must source the shared ModeU5 tool library"
done

per_good_generators=(
	"tools/generate_stock_good_helpers.sh"
	"tools/generate_good_transport_helpers.sh"
	"tools/generate_us10_ui_helpers.sh"
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

printf '%s\n' 'ModeU5 generator and validator convention checks passed'
