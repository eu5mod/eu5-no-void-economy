#!/usr/bin/env python3
"""Compatibility entry point for CMM/static contract validation.

The CMM surface, review-popup registration, and US-17/US-20 static contracts are
validated together so CI and local runs check the same assertions. Importing the
stacked validator installs the curve-model contract overrides before the retained
legacy ``main`` is executed.
"""

from __future__ import annotations

import validate_ci_static_contracts as validator


if __name__ == "__main__":
    raise SystemExit(validator.legacy.main())
