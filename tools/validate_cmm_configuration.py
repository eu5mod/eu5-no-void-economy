#!/usr/bin/env python3
"""Compatibility entry point for CMM/static contract validation.

The CMM surface, review-popup registration, and US-17/US-20 static contracts are
now validated together so CI and local runs check the same assertions.
"""

from __future__ import annotations

from validate_ci_static_contracts import main


if __name__ == "__main__":
    raise SystemExit(main())
