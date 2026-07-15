#!/usr/bin/env python3
"""Compile #188 political and minting edge cases into one composed CBG spec."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def build_spec(args: argparse.Namespace) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="cbp-cbg-political-") as temporary:
        staged = Path(temporary) / "package"
        run([
            "python3", str(args.repo_root / "tools/generate_us177_minting_overrides.py"),
            "--game-root", str(args.game_root), "--package-root", str(staged),
            "--multiplier", args.minting_multiplier,
        ])
        run([
            "python3", str(args.repo_root / "tools/generate_political_reward_overrides.py"),
            "--game-root", str(args.game_root), "--package-root", str(staged),
            "--skip-central-default-values",
        ])
        minting = json.loads(
            (staged / "cbp_generated/us177_minting_income_manifest.json").read_text()
        )
        political = json.loads(
            (staged / "cbp_generated/political_reward_overrides_manifest.json").read_text()
        )
        if args.minting_discovery_manifest:
            args.minting_discovery_manifest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                staged / "cbp_generated/us177_minting_income_manifest.json",
                args.minting_discovery_manifest,
            )
        if args.political_discovery_manifest:
            args.political_discovery_manifest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                staged / "cbp_generated/political_reward_overrides_manifest.json",
                args.political_discovery_manifest,
            )
        paths = {entry["path"] for entry in minting["files"]}
        paths.update(
            entry["path"] if entry.get("package_relative") else f"in_game/{entry['path']}"
            for entry in political["files"]
        )
        transformations = []
        for relative in sorted(paths):
            output = staged / relative
            source = args.game_root / relative
            if not output.is_file() or not source.is_file():
                raise ValueError(f"Composed CBG staging/source missing for {relative}")
            transformations.append({
                "file": relative,
                "object": "",
                "field": "__file__",
                "operation": "replace_file",
                "value": output.read_text(encoding="utf-8"),
                "provenance": "preserve",
                "render_mode": "provided",
            })
        return {
            "schema_version": 1,
            "mod_id": "cbp-economy-rebalance-political-minting",
            "transformations": transformations,
            "scope_contract": {
                "owned_outputs": sorted(paths),
                "phase": "political-and-minting-composition",
                "edge_case_compilers": [
                    "generate_us177_minting_overrides.py",
                    "generate_political_reward_overrides.py",
                ],
                "central_default_values": "delegated-to-focused-cbg-family",
                "building_types": "delegated-to-focused-cbg-building-family",
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--minting-multiplier", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minting-discovery-manifest", type=Path)
    parser.add_argument("--political-discovery-manifest", type=Path)
    args = parser.parse_args()
    payload = build_spec(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Generated {args.output} with {len(payload['transformations'])} "
        "composed political/minting outputs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
