# ================================================================
#  love_v4.ui.assistant_window
#  ----------------------------------------------------------------
#  The main CustomTkinter application window for LOVE v4.
#
#  Layout
#  ──────
#  ┌─────────────────────────────────┐
#  │  ◈ LOVE v4          [— □ ✕]    │  ← title bar
#  ├─────────────────────────────────┤
#  │                                 │
#  │   [conversation history]        │  ← ChatHistory (scrollable)
#  │                                 │
#  ├─────────────────────────────────┤
#  │  ⬤ SLEEPING                    │  ← StatusBar
#  ├─────────────────────────────────┤
#  │  [ Type a command…    ]  [ → ]  │  ← TextCommandBar
#  ├─────────────────────────────────┤
#  │       [ 🎤  LISTEN ]            │  ← MicButton
#  └─────────────────────────────────┘
#
#  Thread safety
#  ─────────────
#  Controller callbacks arrive on worker threads.
#  All UI mutations are marshalled back to the main thread via
#  self.after(0, callable) — the standard Tk idiom.
# ================================================================

from __future__ import annotations

import sys
import threading
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from ui.widgets import (
    COLORS, FONT_TITLE, FONT_LABEL, FONT_MESSAGE,
    ChatHistory, StatusBar, MicButton, TextCommandBar,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AssistantWindow(ctk.CTk):
    """
    The main LOVE v4 application window.

    Parameters
    ----------
    controller_factory : callable that returns an initialised controller
                         once the window is ready.  Passed a reference
                         to this window so it can wire up callbacks.
    """

    def __init__(self, controller_factory) -> None:
        super().__init__()

        self._setup_window()
        self._build_ui()
        self._controller = controller_factory(self)
        self._wire_speak_callback()

        # Show a welcome message and auto-start the continuous loop
        self.after(200, lambda: self._add_love_message(
            "Hello! I'm LOVE v4. Say 'hey love' to wake me, or type a command."
        ))
        self.after(800, self._controller.start_listening)

    # ── Window setup ─────────────────────────────────────────

    def _setup_window(self) -> None:
        self.title("LOVE v4")
        self.geometry("560x720")
        self.minsize(480, 580)
        self.configure(fg_color=COLORS["bg"])
        self.resizable(True, True)

        # Centre on screen
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        x = (w - 560) // 2
        y = (h - 720) // 2
        self.geometry(f"560x720+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)   # chat expands

        # ── Header ───────────────────────────────────────────
        header = ctk.CTkFrame(
            self,
            fg_color     = COLORS["panel"],
            corner_radius = 0,
            border_width  = 0,
        )
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
        header.grid_columnconfigure(0, weight=1)

        # Decorative top accent line
        accent_bar = tk.Frame(header, bg=COLORS["accent"], height=2)
        accent_bar.pack(fill="x", side="top")

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(
            title_row,
            text       = "◈",
            font       = ("Courier New", 18),
            text_color = COLORS["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row,
            text       = "LOVE v4",
            font       = FONT_TITLE,
            text_color = COLORS["text"],
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text       = "Living Omni Voice Ecosystem",
            font       = ("Courier New", 9),
            text_color = COLORS["muted"],
        ).pack(side="left", padx=(12, 0), pady=(6, 0))

        # Command counter (top right)
        self._cmd_count_label = ctk.CTkLabel(
            title_row,
            text       = "",
            font       = FONT_LABEL,
            text_color = COLORS["label"],
        )
        self._cmd_count_label.pack(side="right")

        # ── Chat history ──────────────────────────────────────
        self._chat = ChatHistory(self)
        self._chat.grid(
            row=1, column=0,
            padx=12, pady=(8, 6),
            sticky="nsew",
        )

        # ── Status bar ────────────────────────────────────────
        self._status = StatusBar(self)
        self._status.grid(
            row=2, column=0,
            padx=12, pady=(0, 6),
            sticky="ew",
        )

        # ── Text input ────────────────────────────────────────
        self._text_bar = TextCommandBar(self, on_submit=self._on_text_command)
        self._text_bar.grid(
            row=3, column=0,
            padx=12, pady=(0, 6),
            sticky="ew",
        )

        # ── Mic button ────────────────────────────────────────
        self._mic_btn = MicButton(self, command=self._on_mic_press)
        self._mic_btn.grid(
            row=4, column=0,
            padx=80, pady=(0, 16),
            sticky="ew",
        )

    # ── Controller wiring ────────────────────────────────────

    def _wire_speak_callback(self) -> None:
        """
        After the controller is created, patch extended_browser and
        close_commands to use controller.respond for UI feedback.
        """
        from assistant.commands import extended_browser, close_commands
        extended_browser.set_speak(self._controller.respond)
        close_commands.set_speak(self._controller.respond)

    # ── Public callbacks (called by controller) ───────────────

    def on_user_message(self, text: str) -> None:
        """Thread-safe: add a user bubble."""
        self.after(0, lambda: self._add_user_message(text))

    def on_love_message(self, text: str) -> None:
        """Thread-safe: add an assistant bubble."""
        self.after(0, lambda: self._add_love_message(text))

    def on_state_change(self, state) -> None:
        """Thread-safe: update status bar."""
        from assistant.controller import AssistantState
        mapping = {
            AssistantState.SLEEPING:   "sleeping",
            AssistantState.ACTIVE:     "listening",
            AssistantState.PROCESSING: "processing",
        }
        status_str = mapping.get(state, "sleeping")
        self.after(0, lambda: self._update_status(status_str))

        # Toggle mic button appearance
        is_active = state == AssistantState.ACTIVE
        self.after(0, lambda: self._mic_btn.set_active(is_active))

    def on_error(self, message: str) -> None:
        """Thread-safe: show error in chat."""
        self.after(0, lambda: self._add_love_message(f"Error: {message}"))
        self.after(0, lambda: self._status.set_status("error"))
        self.after(2000, lambda: self._status.set_status("sleeping"))

    # ── Internal UI helpers ───────────────────────────────────

    def _add_user_message(self, text: str) -> None:
        self._chat.add_message("user", text)
        self._update_cmd_count()

    def _add_love_message(self, text: str) -> None:
        self._chat.add_message("love", text)

    def _update_status(self, status: str) -> None:
        self._status.set_status(status)

    def _update_cmd_count(self) -> None:
        count = len(self._controller.memory)
        self._cmd_count_label.configure(
            text=f"{count} cmd{'s' if count != 1 else ''}"
        )

    # ── Event handlers ────────────────────────────────────────

    def _on_mic_press(self) -> None:
        from assistant.controller import AssistantState
        if self._controller._state == AssistantState.SLEEPING:
            # Start the continuous loop if it is not already running
            self._controller.start_listening()
        else:
            # Active or processing: force back to sleep
            self._controller.stop()

    def _on_text_command(self, text: str) -> None:
        self._controller.type_command(text)

    def _on_close(self) -> None:
        self._controller.stop()
        self.destroy()
        sys.exit(0)
