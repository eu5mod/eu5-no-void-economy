#!/usr/bin/env bash

# Canonical ModeU5 good registry used by generators.
# Keep this list aligned with the vanilla goods covered by ModeU5 stock helpers.
modeu5_goods=(
	cotton sugar tobacco
	tar porcelain naval_supplies firearms cannons weaponry glass steel cloth
	fine_cloth liquor beer paper books jewelry leather tools masonry
	lacquerware pottery furniture
	horses clay sand coal iron copper goods_gold silver stone tin lead silk
	dyes incense tea cocoa coffee fiber_crops ivory lumber salt medicaments
	gems pearls amber saltpeter alum wine elephants marble mercury saffron
	pepper cloves chili
	wool wild_game fur fish wheat maize rice millet legumes potato livestock
	olives fruit beeswax
	slaves_goods
)


# Static goods transport costs used by generated US-10 trade-capacity helpers.
# Vanilla defaults transport_cost to 1 when the field is omitted. Runtime tests
# show that `transport_cost` is not script-readable from goods scope, so the
# generator emits literal per-good constants instead of reading the goods
# database at runtime.
modeu5_good_transport_cost() {
	case "$1" in
		dyes|incense|medicaments|gems|saffron|pepper|cloves|chili|porcelain|glass|cloth|fine_cloth|liquor|beer|paper|books|jewelry|tools|lacquerware|pottery|furniture)
			printf '%s\n' '0.5'
			;;
		horses|clay|sand|coal|goods_gold|silver|stone|legumes|fruit)
			printf '%s\n' '2'
			;;
		marble)
			printf '%s\n' '3'
			;;
		elephants)
			printf '%s\n' '5'
			;;
		firearms|cannons)
			printf '%s\n' '1.0'
			;;
		*)
			printf '%s\n' '1'
			;;
	esac
}

modeu5_good_transport_cost_defaulted() {
	case "$1" in
		horses|clay|sand|coal|iron|copper|goods_gold|silver|stone|tin|lead|dyes|incense|lumber|medicaments|gems|elephants|marble|saffron|pepper|cloves|chili|porcelain|firearms|cannons|glass|steel|cloth|fine_cloth|liquor|beer|paper|books|jewelry|tools|lacquerware|pottery|furniture|legumes|fruit)
			printf '%s\n' '0'
			;;
		*)
			printf '%s\n' '1'
			;;
	esac
}
