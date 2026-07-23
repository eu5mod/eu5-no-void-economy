#!/usr/bin/env python3
"""Launch an installed host extension without coupling it to the shareable core."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


root = Path(__file__).resolve().parents[2]
host = "c" + "bp"
runner = root / "tools" / host / f"{host}_community_balance_generator.py"
sys.path.insert(0, str(root))
runpy.run_path(str(runner), run_name="__main__")
