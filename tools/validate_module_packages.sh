#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

descriptors=(
	"descriptor.mod"
	"packages/modeu5_economy_rebalance/descriptor.mod"
	"packages/modeu5_trade_rebalance/descriptor.mod"
	"packages/modeu5_war_rebalance/descriptor.mod"
)

metadata_files=(
	".metadata/metadata.json"
	"packages/modeu5_economy_rebalance/.metadata/metadata.json"
	"packages/modeu5_trade_rebalance/.metadata/metadata.json"
	"packages/modeu5_war_rebalance/.metadata/metadata.json"
)

expected_names=(
	"No Void Economy"
	"Rebalance Economy"
	"Rebalance Estate Power"
	"Rebalance Early Blobbing"
)

expected_ids=(
	"modeu5_core"
	"modeu5_economy_rebalance"
	"modeu5_trade_rebalance"
	"modeu5_war_rebalance"
)

expected_description_prefixes=(
	"REQUIRED FOR MODEU5 SAVES."
	"CAMPAIGN SETUP ONLY."
	"CAMPAIGN SETUP ONLY."
	"CAMPAIGN SETUP ONLY."
)

for index in "${!descriptors[@]}"; do
	descriptor="${descriptors[$index]}"
	expected_name="${expected_names[$index]}"

	test -f "$descriptor"
	rg -q "^name=\"${expected_name}\"$" "$descriptor"
	rg -q '^version="0\.1\.0"$' "$descriptor"
done

if command -v jq >/dev/null 2>&1; then
	jq empty "${metadata_files[@]}"
	for index in "${!metadata_files[@]}"; do
		metadata_file="${metadata_files[$index]}"
		expected_id="${expected_ids[$index]}"
		expected_name="${expected_names[$index]}"
		expected_description_prefix="${expected_description_prefixes[$index]}"

		test "$(jq -r '.id' "$metadata_file")" = "$expected_id"
		test "$(jq -r '.name' "$metadata_file")" = "$expected_name"
		test "$(jq -r '.version' "$metadata_file")" = "0.1.0"
		test "$(jq -r '.short_description | startswith($prefix)' --arg prefix "$expected_description_prefix" "$metadata_file")" = "true"
		jq -e '.short_description | test("before starting a campaign|mid-campaign is unsupported")' "$metadata_file" >/dev/null
	done
else
	printf 'WARNING: jq is unavailable; JSON syntax was not checked.\n' >&2
fi

if rg -n 'set_global_variable = modeu5_(economy|trade|war)_rebalance_loaded' in_game; then
	printf 'Core must not manufacture companion package markers.\n' >&2
	exit 1
fi

rg -q 'set_global_variable = modeu5_economy_rebalance_loaded' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt
rg -q 'set_global_variable = modeu5_trade_rebalance_loaded' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt
rg -q 'set_global_variable = modeu5_war_rebalance_loaded' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt
rg -q 'name = modeu5_core_package_version' \
	in_game/common/scripted_effects/modeu5_configuration_effects.txt
rg -q 'name = modeu5_economy_package_version' \
	packages/modeu5_economy_rebalance/in_game/common/on_action/modeu5_economy_package_on_actions.txt
rg -q 'name = modeu5_trade_package_version' \
	packages/modeu5_trade_rebalance/in_game/common/on_action/modeu5_trade_package_on_actions.txt
rg -q 'name = modeu5_war_package_version' \
	packages/modeu5_war_rebalance/in_game/common/on_action/modeu5_war_package_on_actions.txt

printf 'ModeU5 package descriptors and package-owned markers are valid.\n'
