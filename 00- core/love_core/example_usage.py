#!/usr/bin/env python3
# ================================================================
#  love_core — Example Usage
#  ----------------------------------------------------------------
#  Demonstrates three patterns for building with love_core:
#
#    1. Minimal setup (global registry, decorator)
#    2. Isolated setup (custom registry per assistant)
#    3. Simulated dispatch loop (no microphone required)
#
#  Run:  python example_usage.py
# ================================================================

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


# ════════════════════════════════════════════════════════════════
#  PATTERN 1 — Decorator with the global default registry
#  ─────────────────────────────────────────────────────────────
#  Use this pattern for quick prototypes or single-file scripts.
# ════════════════════════════════════════════════════════════════

from love_core.command_registry import command, default_registry
from love_core.router           import Router, DispatchStatus
from love_core.memory.session   import SessionMemory
from love_core.utils.logger     import get_logger

log = get_logger("example")


# Register an exact command with the decorator
@command("greet", description="Say hello.", tags=["demo"])
def greet():
    print("[LOVE] Hello! How can I help you?")


# Register a prefix command — receives the remainder as an argument
@command("say", is_prefix=True, description="Repeat anything back.", tags=["demo"])
def say_back(text: str):
    print(f"[LOVE] You said: {text}")


# Register a prefix command for search
@command("look up", is_prefix=True, description="Simulate a search.", tags=["demo"])
def fake_search(query: str):
    print(f"[LOVE] Searching for: {query}")


def demo_global_registry():
    print("\n" + "═" * 60)
    print("  PATTERN 1 — Global Registry + Decorator")
    print("═" * 60)

    router = Router()   # uses default_registry automatically
    router.set_fallback(lambda text: print(f"[LOVE] No command found for: '{text}'"))

    test_inputs = [
        "greet",
        "say good morning",
        "look up python tutorials",
        "unknown command xyz",
    ]

    for utterance in test_inputs:
        print(f"\n  Input: '{utterance}'")
        result = router.dispatch(utterance)
        print(f"  Status: {result.status.name}")


# ════════════════════════════════════════════════════════════════
#  PATTERN 2 — Isolated registry (recommended for assistants)
#  ─────────────────────────────────────────────────────────────
#  Each assistant version gets its own CommandRegistry.
#  Command modules are loaded explicitly.
# ════════════════════════════════════════════════════════════════

from love_core.command_registry import CommandRegistry
from love_core.commands         import browser, apps, system


def demo_custom_registry():
    print("\n" + "═" * 60)
    print("  PATTERN 2 — Custom Registry + Module Bundles")
    print("═" * 60)

    # Create an isolated registry for this assistant
    reg    = CommandRegistry(name="love_v4_demo")
    router = Router(registry=reg)
    mem    = SessionMemory(max_entries=50)

    # Load built-in command bundles
    browser.register_all(registry=reg)
    apps.register_all(registry=reg)
    system.register_all(registry=reg)

    # Add a custom command inline
    def custom_hello():
        print("[v4] Hey! This is LOVE v4.")

    reg.register("hello love", custom_hello, description="Custom greeting", tags=["v4"])

    # Fallback: unrecognised → Google search (simulated here)
    def fallback(text: str):
        print(f"[v4] Fallback: would search Google for '{text}'")
        mem.record(text, resolved=False)

    router.set_fallback(fallback)

    print(f"\n  Registry: {reg}")
    print(f"  Commands loaded: {len(reg)}")

    # Simulate dispatching commands
    test_inputs = [
        "hello love",
        "open youtube",
        "search python decorators",
        "time",
        "what is the meaning of life",   # triggers fallback
    ]

    for utterance in test_inputs:
        print(f"\n  Input: '{utterance}'")
        result = router.dispatch(utterance)
        mem.record(utterance, resolved=result.matched)
        print(f"  Status: {result.status.name}")

    print(f"\n  Session summary: {mem.summary()}")


# ════════════════════════════════════════════════════════════════
#  PATTERN 3 — Introspection
#  ─────────────────────────────────────────────────────────────
#  List all registered commands by tag.
# ════════════════════════════════════════════════════════════════

def demo_introspection():
    print("\n" + "═" * 60)
    print("  PATTERN 3 — Registry Introspection")
    print("═" * 60)

    reg = CommandRegistry("introspect_demo")
    browser.register_all(registry=reg)
    system.register_all(registry=reg)

    print(f"\n  Total commands: {len(reg)}")

    print("\n  Browser commands:")
    for entry in reg.commands_by_tag("browser"):
        kind = "prefix" if entry.is_prefix else "exact "
        print(f"    [{kind}] '{entry.phrase}'  —  {entry.description}")

    print("\n  All phrases (sorted):")
    for phrase in reg.phrases():
        print(f"    • {phrase}")


# ════════════════════════════════════════════════════════════════
#  PATTERN 4 — Live voice loop skeleton (requires microphone)
#  ─────────────────────────────────────────────────────────────
#  This is the template a real assistant (love_v4) would use.
#  It is NOT run by default to avoid requiring a microphone.
# ════════════════════════════════════════════════════════════════

VOICE_LOOP_TEMPLATE = '''
from love_core.voice.listen      import Listener
from love_core.voice.speak       import Speaker
from love_core.command_registry  import CommandRegistry
from love_core.router            import Router
from love_core.memory.session    import SessionMemory
from love_core.commands          import browser, apps, system

WAKE_WORDS = ["hey love", "hello love"]
STOP_WORD  = "bye love"

def run():
    reg     = CommandRegistry("love_v4")
    router  = Router(registry=reg)
    mem     = SessionMemory()
    mic     = Listener()
    tts     = Speaker()

    browser.register_all(registry=reg)
    apps.register_all(registry=reg)
    system.register_all(registry=reg)

    router.set_fallback(lambda text: tts.speak(f"Searching for {text}"))

    tts.speak("LOVE v4 ready.")
    awake = False

    while True:
        heard = mic.listen()
        if heard is None:
            continue

        if not awake:
            if any(w in heard for w in WAKE_WORDS):
                awake = True
                tts.speak("Listening.")
        else:
            if STOP_WORD in heard:
                tts.speak("Goodbye.")
                break
            result = router.dispatch(heard)
            mem.record(heard, resolved=result.matched)
            awake = False   # one command per wake cycle

if __name__ == "__main__":
    run()
'''


# ════════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_global_registry()
    demo_custom_registry()
    demo_introspection()

    print("\n" + "═" * 60)
    print("  PATTERN 4 — Voice Loop Template (not run here)")
    print("  Copy the template into your love_v4/main.py")
    print("═" * 60)
    print(VOICE_LOOP_TEMPLATE)
