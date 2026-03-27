#!/usr/bin/env python3
# ================================================================
#  love_v4 — Main Entry Point
#  ----------------------------------------------------------------
#  Run:  python main.py
#
#  Architecture in one paragraph
#  ──────────────────────────────
#  main.py creates the AssistantWindow, which takes a
#  controller_factory callable.  The factory builds an
#  AssistantController wired to the window's callback methods
#  (on_user_message, on_love_message, on_state_change, on_error).
#  The controller owns all love_core components: registry, router,
#  listener, speaker, and memory.  The window owns zero business
#  logic — it is a pure view.
# ================================================================

import sys
import os

# Ensure project root and love_core parent are on the path.
# Adjust LOVE_ROOT if your folder layout differs.
_HERE      = os.path.dirname(os.path.abspath(__file__))
_LOVE_ROOT = os.path.dirname(_HERE)   # parent of love_v4/

for path in [_HERE, _LOVE_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from assistant.controller import AssistantController
from ui.assistant_window  import AssistantWindow


def controller_factory(window: AssistantWindow) -> AssistantController:
    """
    Build the controller wired to *window*'s callback methods.
    Called by AssistantWindow after the UI is ready.
    """
    return AssistantController(
        on_user_message = window.on_user_message,
        on_love_message = window.on_love_message,
        on_state_change = window.on_state_change,
        on_error        = window.on_error,
    )


def main() -> None:
    app = AssistantWindow(controller_factory=controller_factory)
    app.mainloop()


if __name__ == "__main__":
    main()
