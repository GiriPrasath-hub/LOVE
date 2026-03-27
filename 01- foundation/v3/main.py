#!/usr/bin/env python3
# ============================================================
#  LOVE v3 — Entry Point
#  Run:  python main.py
# ============================================================

import sys
import os

# Ensure the project root is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from core.love_core import LOVECore


def main() -> None:
    assistant = LOVECore()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\n[LOVE] Interrupted by user.")
    finally:
        print("[LOVE] Session ended.")


if __name__ == "__main__":
    main()
