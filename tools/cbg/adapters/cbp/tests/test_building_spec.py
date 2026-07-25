from __future__ import annotations

import unittest

from tools.cbg.adapters.cbp.generate_cbp_cbg_building_spec import (
    build_injection_fragment,
)


class BuildingSpecTests(unittest.TestCase):
    def test_modifier_injection_uses_delta_not_absolute_target(self):
        source = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2",
            "\t}",
            "}",
        ]
        transformed = [
            "marketplace = {",
            "\tmodifier = {",
            "\t\tlocal_merchant_capacity = 2.3 # VANILLA = 2",
            "\t}",
            "}",
        ]

        self.assertEqual(
            build_injection_fragment(source, transformed, "marketplace"),
            [
                "marketplace = {",
                "\tmodifier = {",
                (
                    "\t\tlocal_merchant_capacity = 0.3 "
                    "# VANILLA = 2; TARGET = 2.3"
                ),
                "\t}",
                "}",
            ],
        )

    def test_stockpile_capacity_is_cancelled_with_negative_delta(self):
        source = [
            "warehouse = {",
            "\tmarket_center_modifier = {",
            "\t\tmaximum_stockpile_capacity = 200",
            "\t}",
            "}",
        ]
        transformed = [
            "warehouse = {",
            "\tmarket_center_modifier = {",
            "\t\t# maximum_stockpile_capacity = 200",
            "\t}",
            "}",
        ]

        self.assertEqual(
            build_injection_fragment(source, transformed, "warehouse"),
            [
                "warehouse = {",
                "\tmarket_center_modifier = {",
                (
                    "\t\tmaximum_stockpile_capacity = -200.0 "
                    "# VANILLA = 200; TARGET = 0"
                ),
                "\t}",
                "}",
            ],
        )


if __name__ == "__main__":
    unittest.main()
