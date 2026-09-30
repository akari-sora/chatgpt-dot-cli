#!/usr/bin/env python3
"""Full read probe. Prefer `python -m chatgpt_dot` for day-to-day use."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chatgpt_dot.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["probe"]))
