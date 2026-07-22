#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_in_method(path: str, method: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    marker = f"    def {method}(self):"
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"{path}: missing method {method}")
    next_method = text.find("\n    def ", start + len(marker))
    end = len(text) if next_method < 0 else next_method
    body = text[start:end]
    if new in body:
        return
    count = body.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}:{method}: expected one replacement, found {count}"
        )
    text = text[:start] + body.replace(old, new, 1) + text[end:]
    target.write_text(text, encoding="utf-8")


reference = Path(
    "tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"
)
reference.parent.mkdir(parents=True, exist_ok=True)
reference.write_text(
    """# Reviewed Vanilla reference for the optional CBP development stockpile policy.
# Source path when reviewed: game/main_menu/common/static_modifiers/location.txt
# Expected policy field: development.maximum_stockpile_capacity = 5
# This is an object-level comparison snapshot, not a complete Vanilla file.

development = {
\tgame_data = {
\t\tcategory = location
\t}
\tlocal_population_capacity_modifier = 0.025
\tlocal_distance_from_capital_speed_propagation = 0.005
\tlocal_supply_limit_modifier = 0.02
\tblockade_force_required = 0.01
\tlocal_migration_attraction = 0.0025
\tlocal_trade_center_power = 0.001
\tlocal_institution_growth_modifier = 0.002
\tlocal_construction_speed = 0.01
\tlocal_monthly_food_modifier = 0.01
\tfree_building_levels = 1
\tlocal_max_rgo_size = 0.1
\tlocal_life_expectancy = 0.1
\toccupation_time = 0.01
\tlocal_build_buildings_cost = -0.001
\tmaximum_stockpile_capacity = 5
}
""",
    encoding="utf-8",
)

adapter = "tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py"
replace_once(
    adapter,
    'OUTPUT = "main_menu/common/static_modifiers/cbp_location.txt"\n',
    'OUTPUT = "main_menu/common/static_modifiers/cbp_location.txt"\n'
    'REVIEWED_DEVELOPMENT_REFERENCE = (\n'
    '    REPO_ROOT\n'
    '    / "tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"\n'
    ')\n'
    'DEFAULT_GENERATED_OUTPUT = REPO_ROOT / OUTPUT\n',
)
replace_once(
    adapter,
    '''def vanilla_link(source: Path, line_number: int | None = None) -> str:
    link = source.expanduser().resolve().as_uri()
    return f"{link}#L{line_number}" if line_number is not None else link


''',
    '''def file_link(path: Path, line_number: int | None = None) -> str:
    link = path.expanduser().resolve().as_uri()
    return f"{link}#L{line_number}" if line_number is not None else link


def warn_location_policy_skipped(
    *,
    source: Path,
    generated_output: Path,
    reason: str,
    effect: str,
) -> None:
    warn(
        "NON-FATAL: optional location transformation skipped; generation continues.\n"
        "      Policy: development.maximum_stockpile_capacity\n"
        f"      Reason: {reason}\n"
        f"      Effect: {effect}\n"
        "      Command status: dev_prepare_game is not aborted and will continue to "
        "validation and installation unless a later step fails.\n"
        f"      Current Vanilla source: {file_link(source)}\n"
        f"      Previous reviewed reference: {file_link(REVIEWED_DEVELOPMENT_REFERENCE)}\n"
        f"      Generated output: {file_link(generated_output)} "
        "(the development transformation will be absent)"
    )


def warn_location_policy_changed(
    *,
    source: Path,
    generated_output: Path,
    line_number: int,
    current_value: str,
) -> None:
    warn(
        "NON-FATAL: reviewed Vanilla value changed; generation continues.\n"
        "      Policy: development.maximum_stockpile_capacity\n"
        f"      Previous reviewed value: {EXPECTED_DEVELOPMENT_STOCKPILE_CAPACITY}\n"
        f"      Current Vanilla value: {current_value}\n"
        "      Effect: CBP comments the current Vanilla assignment in the generated "
        "development object; the command is not aborted.\n"
        f"      Current Vanilla source: {file_link(source, line_number)}\n"
        f"      Previous reviewed reference: {file_link(REVIEWED_DEVELOPMENT_REFERENCE)}\n"
        f"      Generated output: {file_link(generated_output)}"
    )


''',
)
replace_once(
    adapter,
    '''def source_transformations(
    source: Path,
    replacement_targets: list[ReplacementTarget],
) -> list[dict[str, object]]:
''',
    '''def source_transformations(
    source: Path,
    replacement_targets: list[ReplacementTarget],
    generated_output: Path = DEFAULT_GENERATED_OUTPUT,
) -> list[dict[str, object]]:
''',
)
replace_once(
    adapter,
    '''    if development_range is None:
        warn(
            "Vanilla development static modifier is not exposed by this EU5 version; "
            "skipping its stockpile-capacity transformation. "
            f"Review Vanilla source: {vanilla_link(source)}"
        )
        return transformations
''',
    '''    if development_range is None:
        warn_location_policy_skipped(
            source=source,
            generated_output=generated_output,
            reason="the Vanilla 'development' object is absent in this EU5 version",
            effect=(
                "only this policy is omitted; all other applicable location "
                "transformations are still generated"
            ),
        )
        return transformations
''',
)
replace_once(
    adapter,
    '''    if development_assignment is None:
        warn(
            "Vanilla development.maximum_stockpile_capacity is not exposed by this "
            "EU5 version; skipping this location transformation. "
            f"Review Vanilla source: {vanilla_link(source)}"
        )
        return transformations
''',
    '''    if development_assignment is None:
        warn_location_policy_skipped(
            source=source,
            generated_output=generated_output,
            reason=(
                "the Vanilla 'development' object exists, but "
                "maximum_stockpile_capacity is absent"
            ),
            effect=(
                "only this field transformation is omitted; all other applicable "
                "location transformations are still generated"
            ),
        )
        return transformations
''',
)
replace_once(
    adapter,
    '''        warn(
            "Vanilla value changed: development.maximum_stockpile_capacity was "
            f"reviewed at {EXPECTED_DEVELOPMENT_STOCKPILE_CAPACITY} and is now "
            f"{current_value}. CBP will continue and comment the current value. "
            f"Review Vanilla source: {vanilla_link(source, line_index + 1)}"
        )
''',
    '''        warn_location_policy_changed(
            source=source,
            generated_output=generated_output,
            line_number=line_index + 1,
            current_value=current_value,
        )
''',
)
replace_once(
    adapter,
    '''def build_spec(source_file: Path | None = None) -> dict[str, object]:
    transformations = (
        source_transformations(source_file, configured_replacement_targets())
        if source_file is not None
        else fallback_transformations()
    )
''',
    '''def build_spec(
    source_file: Path | None = None,
    generated_output: Path = DEFAULT_GENERATED_OUTPUT,
) -> dict[str, object]:
    transformations = (
        source_transformations(
            source_file,
            configured_replacement_targets(),
            generated_output,
        )
        if source_file is not None
        else fallback_transformations()
    )
''',
)
replace_once(
    adapter,
    '''    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_file = args.source_file.resolve() if args.source_file else source_from_environment()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_spec(source_file), indent=2, sort_keys=True) + "\n",
''',
    '''    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--generated-file",
        type=Path,
        default=DEFAULT_GENERATED_OUTPUT,
        help="Expected generated CBG output path, used in actionable warnings.",
    )
    args = parser.parse_args()
    source_file = args.source_file.resolve() if args.source_file else source_from_environment()
    generated_output = args.generated_file.expanduser().resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            build_spec(source_file, generated_output),
            indent=2,
            sort_keys=True,
        )
        + "\n",
''',
)

shell = "tools/generate_cbp_location_overrides.sh"
replace_once(
    shell,
    'output_file="$repo_root/main_menu/common/static_modifiers/cbp_location.txt"\n',
    'output_file="$repo_root/main_menu/common/static_modifiers/cbp_location.txt"\n'
    'reviewed_reference="$repo_root/tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"\n',
)
replace_once(
    shell,
    '''python3 - "$source_file" "$output_file" \
\t"$expensive_food_growth" "$cheap_food_growth" \
\t"$market_center_stockpile" "$surplus_jobs_attraction" <<'PY'
''',
    '''python3 - "$source_file" "$output_file" "$reviewed_reference" \
\t"$expensive_food_growth" "$cheap_food_growth" \
\t"$market_center_stockpile" "$surplus_jobs_attraction" <<'PY'
''',
)
replace_once(
    shell,
    '''source_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
expected_development_stockpile = os.environ.get(
''',
    '''source_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
reviewed_reference_path = Path(sys.argv[3])
expected_development_stockpile = os.environ.get(
''',
)
replace_once(
    shell,
    '''    "expensive_food_in_location": ("local_population_growth", "replace", sys.argv[3]),
    "cheap_food_in_location": ("local_population_growth", "replace", sys.argv[4]),
    "market_center": ("maximum_stockpile_capacity", "replace", sys.argv[5]),
    "surplus_jobs": ("local_migration_attraction", "replace", sys.argv[6]),
''',
    '''    "expensive_food_in_location": ("local_population_growth", "replace", sys.argv[4]),
    "cheap_food_in_location": ("local_population_growth", "replace", sys.argv[5]),
    "market_center": ("maximum_stockpile_capacity", "replace", sys.argv[6]),
    "surplus_jobs": ("local_migration_attraction", "replace", sys.argv[7]),
''',
)
replace_once(
    shell,
    '''def vanilla_link(line_number: int | None = None) -> str:
    link = source_path.expanduser().resolve().as_uri()
    return f"{link}#L{line_number}" if line_number is not None else link


''',
    '''def file_link(path: Path, line_number: int | None = None) -> str:
    link = path.expanduser().resolve().as_uri()
    return f"{link}#L{line_number}" if line_number is not None else link


def warn_location_policy_skipped(reason: str, effect: str) -> None:
    warn(
        "NON-FATAL: optional location transformation skipped; generation continues.\n"
        "      Policy: development.maximum_stockpile_capacity\n"
        f"      Reason: {reason}\n"
        f"      Effect: {effect}\n"
        "      Command status: generation is not aborted; callers such as "
        "dev_prepare_game continue to validation and installation unless a later "
        "step fails.\n"
        f"      Current Vanilla source: {file_link(source_path)}\n"
        f"      Previous reviewed reference: {file_link(reviewed_reference_path)}\n"
        f"      Generated output: {file_link(output_path)} "
        "(the development transformation will be absent)"
    )


def warn_location_policy_changed(line_number: int, current_value: str) -> None:
    warn(
        "NON-FATAL: reviewed Vanilla value changed; generation continues.\n"
        "      Policy: development.maximum_stockpile_capacity\n"
        f"      Previous reviewed value: {expected_development_stockpile}\n"
        f"      Current Vanilla value: {current_value}\n"
        "      Effect: CBP comments the current Vanilla assignment in the generated "
        "development object; generation is not aborted.\n"
        f"      Current Vanilla source: {file_link(source_path, line_number)}\n"
        f"      Previous reviewed reference: {file_link(reviewed_reference_path)}\n"
        f"      Generated output: {file_link(output_path)}"
    )


''',
)
replace_once(
    shell,
    '''if "development" not in blocks:
    warn(
        "Vanilla development static modifier is not exposed by this EU5 version; "
        "skipping its stockpile-capacity transformation. "
        f"Review Vanilla source: {vanilla_link()}"
    )
''',
    '''if "development" not in blocks:
    warn_location_policy_skipped(
        "the Vanilla 'development' object is absent in this EU5 version",
        "only this policy is omitted; all other applicable location transformations are still generated",
    )
''',
)
replace_once(
    shell,
    '''    if not matches and name == "development":
        warn(
            "Vanilla development.maximum_stockpile_capacity is not exposed by this "
            "EU5 version; skipping this location transformation. "
            f"Review Vanilla source: {vanilla_link()}"
        )
        continue
''',
    '''    if not matches and name == "development":
        warn_location_policy_skipped(
            "the Vanilla 'development' object exists, but maximum_stockpile_capacity is absent",
            "only this field transformation is omitted; all other applicable location transformations are still generated",
        )
        continue
''',
)
replace_once(
    shell,
    '''            warn(
                "Vanilla value changed: development.maximum_stockpile_capacity was "
                f"reviewed at {expected_development_stockpile} and is now "
                f"{vanilla_value}. CBP will continue and comment the current value. "
                f"Review Vanilla source: {vanilla_link(absolute_line_number)}"
            )
''',
    '''            warn_location_policy_changed(
                absolute_line_number,
                vanilla_value,
            )
''',
)

generate_all = "tools/generate_all.sh"
replace_once(
    generate_all,
    'python3 "$repo_root/tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py" --output "$cbg_location_spec"',
    'python3 "$repo_root/tools/cbg/adapters/cbp/generate_cbp_cbg_location_spec.py" \\
\t\t--output "$cbg_location_spec" \\
\t\t--generated-file "$repo_root/main_menu/common/static_modifiers/cbp_location.txt"',
)

tests = "tools/cbg/adapters/cbp/tests/test_location_static_modifiers.py"
replace_once(
    tests,
    '''        spec = root / "location.json"
        spec_run = subprocess.run(
''',
    '''        candidate_root = root / "candidate"
        candidate = candidate_root / OUTPUT
        spec = root / "location.json"
        spec_run = subprocess.run(
''',
)
replace_once(
    tests,
    '''                "--output",
                str(spec),
            ],
''',
    '''                "--output",
                str(spec),
                "--generated-file",
                str(candidate),
            ],
''',
)
replace_once(
    tests,
    '''        candidate_root = root / "candidate"
        subprocess.run(
''',
    '''        subprocess.run(
''',
)
replace_once(
    tests,
    '''        candidate = candidate_root / OUTPUT
        self.assertEqual(reference.is_file(), candidate.is_file())
''',
    '''        self.assertEqual(reference.is_file(), candidate.is_file())
''',
)

changed_old = '''            expected_message = (
                "Vanilla value changed: development.maximum_stockpile_capacity "
                "was reviewed at 5 and is now 8"
            )
            expected_link = source.resolve().as_uri() + "#L"
            for warning in (legacy_stderr, spec_stderr):
                self.assertIn("[⚠️]", warning)
                self.assertIn(expected_message, warning)
                self.assertIn(expected_link, warning)
                self.assertIn("CBP will continue", warning)
'''
changed_new = '''            root = Path(temporary)
            expected_reference = (
                REPO_ROOT
                / "tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"
            ).resolve().as_uri()
            expected_outputs = (
                (root / "reference/cbp_location.txt").resolve().as_uri(),
                (root / "candidate" / OUTPUT).resolve().as_uri(),
            )
            for warning, expected_output in zip(
                (legacy_stderr, spec_stderr),
                expected_outputs,
                strict=True,
            ):
                self.assertIn("[⚠️] NON-FATAL", warning)
                self.assertIn("reviewed Vanilla value changed", warning)
                self.assertIn("Previous reviewed value: 5", warning)
                self.assertIn("Current Vanilla value: 8", warning)
                self.assertIn(source.resolve().as_uri() + "#L", warning)
                self.assertIn(expected_reference, warning)
                self.assertIn(expected_output, warning)
                self.assertIn("not aborted", warning)
'''
replace_in_method(
    tests,
    "test_changed_vanilla_value_warns_with_link_and_does_not_fail",
    changed_old,
    changed_new,
)

missing_old = '''            for warning in (legacy_stderr, spec_stderr):
                self.assertIn("[⚠️] Vanilla development static modifier", warning)
                self.assertIn(source.resolve().as_uri(), warning)
'''
missing_new = '''            root = Path(temporary)
            expected_reference = (
                REPO_ROOT
                / "tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"
            ).resolve().as_uri()
            expected_outputs = (
                (root / "reference/cbp_location.txt").resolve().as_uri(),
                (root / "candidate" / OUTPUT).resolve().as_uri(),
            )
            for warning, expected_output in zip(
                (legacy_stderr, spec_stderr),
                expected_outputs,
                strict=True,
            ):
                self.assertIn("[⚠️] NON-FATAL", warning)
                self.assertIn("generation continues", warning)
                self.assertIn("only this policy is omitted", warning)
                self.assertIn("dev_prepare_game", warning)
                self.assertIn("Current Vanilla source:", warning)
                self.assertIn(source.resolve().as_uri(), warning)
                self.assertIn("Previous reviewed reference:", warning)
                self.assertIn(expected_reference, warning)
                self.assertIn("Generated output:", warning)
                self.assertIn(expected_output, warning)
'''
replace_in_method(
    tests,
    "test_missing_development_block_warns_and_does_not_fail_generation",
    missing_old,
    missing_new,
)

noop_new = '''            root = Path(temporary)
            expected_reference = (
                REPO_ROOT
                / "tools/cbg/adapters/cbp/reference/vanilla/location_development_reviewed.txt"
            ).resolve().as_uri()
            expected_outputs = (
                (root / "reference/cbp_location.txt").resolve().as_uri(),
                (root / "candidate" / OUTPUT).resolve().as_uri(),
            )
            for warning, expected_output in zip(
                (legacy_stderr, spec_stderr),
                expected_outputs,
                strict=True,
            ):
                self.assertIn("[⚠️] NON-FATAL", warning)
                self.assertIn("generation continues", warning)
                self.assertIn(source.resolve().as_uri(), warning)
                self.assertIn(expected_reference, warning)
                self.assertIn(expected_output, warning)
'''
replace_in_method(
    tests,
    "test_output_file_is_omitted_when_every_policy_is_a_noop",
    missing_old,
    noop_new,
)

print("Applied actionable location-warning UX patch.")
