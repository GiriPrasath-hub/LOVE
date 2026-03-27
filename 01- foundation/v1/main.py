#!/usr/bin/env python3
# ============================================================
#  LOVE v1 — Entry Point
#  Run:  python main.py
# ============================================================

import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from core.love_core import run


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[LOVE] Interrupted. Goodbye!")
