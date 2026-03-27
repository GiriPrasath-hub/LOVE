# ================================================================
#  love_v4.ui.widgets
#  ----------------------------------------------------------------
#  Reusable CustomTkinter widget components for the LOVE v4 UI.
#
#  Components
#  ──────────
#  • ChatBubble     — single message bubble (user / assistant)
#  • ChatHistory    — scrollable conversation log
#  • StatusBar      — animated status indicator
#  • MicButton      — pulsing microphone button
#  • TextCommandBar — keyboard input bar
# ================================================================

from __future__ import annotations

import tkinter as tk
from typing import Callable, Literal

import customtkinter as ctk

# ── Palette ───────────────────────────────────────────────────
COLORS = {
    "bg":           "#0D0F14",
    "panel":        "#13161E",
    "panel_border": "#1E2330",
    "user_bubble":  "#1A2640",
    "user_text":    "#7EB8F7",
    "love_bubble":  "#141A20",
    "love_text":    "#E0E8F0",
    "accent":       "#3D8EF0",
    "accent_glow":  "#1A4A8A",
    "muted":        "#4A5568",
    "error":        "#F05252",
    "success":      "#3DF08E",
    "warning":      "#F0A83D",
    "text":         "#C8D6E8",
    "label":        "#64748B",
}

FONT_TITLE   = ("Courier New", 22, "bold")
FONT_MESSAGE = ("Courier New", 12)
FONT_LABEL   = ("Courier New", 10)
FONT_INPUT   = ("Courier New", 12)
FONT_BUTTON  = ("Courier New", 13, "bold")


# ── Chat bubble ──────────────────────────────────────────────

class ChatBubble(ctk.CTkFrame):
    """
    A single message bubble.

    Parameters
    ----------
    parent  : parent widget
    speaker : "user" or "love"
    text    : message text
    """

    def __init__(
        self,
        parent,
        speaker: Literal["user", "love"],
        text: str,
        **kwargs,
    ) -> None:
        is_user = speaker == "user"

        bg    = COLORS["user_bubble"] if is_user else COLORS["love_bubble"]
        color = COLORS["user_text"]   if is_user else COLORS["love_text"]
        label = "YOU"                 if is_user else "LOVE"
        lc    = COLORS["accent"]      if is_user else COLORS["success"]

        super().__init__(
            parent,
            fg_color   = bg,
            corner_radius = 8,
            border_width  = 1,
            border_color  = COLORS["panel_border"],
            **kwargs,
        )

        self.grid_columnconfigure(0, weight=1)

        # Speaker label
        ctk.CTkLabel(
            self,
            text       = label,
            font       = FONT_LABEL,
            text_color = lc,
            anchor     = "w",
        ).grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")

        # Message text (wrapping)
        ctk.CTkLabel(
            self,
            text         = text,
            font         = FONT_MESSAGE,
            text_color   = color,
            anchor       = "w",
            justify      = "left",
            wraplength   = 440,
        ).grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")


# ── Chat history ─────────────────────────────────────────────

class ChatHistory(ctk.CTkScrollableFrame):
    """
    Scrollable container for ChatBubble widgets.
    Auto-scrolls to the latest message.
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(
            parent,
            fg_color      = COLORS["panel"],
            corner_radius = 10,
            border_width  = 1,
            border_color  = COLORS["panel_border"],
            scrollbar_button_color        = COLORS["accent_glow"],
            scrollbar_button_hover_color  = COLORS["accent"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self._row = 0

    def add_message(
        self,
        speaker: Literal["user", "love"],
        text: str,
    ) -> None:
        """Append a new message bubble and scroll to bottom."""
        bubble = ChatBubble(self, speaker=speaker, text=text)
        bubble.grid(
            row     = self._row,
            column  = 0,
            padx    = 10,
            pady    = (4, 4),
            sticky  = "ew",
        )
        self._row += 1
        # Scroll to latest
        self.after(50, lambda: self._parent_canvas.yview_moveto(1.0))

    def clear(self) -> None:
        """Remove all messages."""
        for widget in self.winfo_children():
            widget.destroy()
        self._row = 0


# ── Status bar ───────────────────────────────────────────────

class StatusBar(ctk.CTkFrame):
    """
    Animated status indicator showing the assistant's current state.
    """

    _STATUS_CONFIG = {
        "sleeping":    ("⬤  SLEEPING",   COLORS["muted"]),
        "listening":   ("◎  LISTENING",  COLORS["accent"]),
        "processing":  ("◈  THINKING",   COLORS["warning"]),
        "speaking":    ("◉  SPEAKING",   COLORS["success"]),
        "error":       ("✕  ERROR",       COLORS["error"]),
    }

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(
            parent,
            fg_color      = COLORS["panel"],
            corner_radius = 8,
            border_width  = 1,
            border_color  = COLORS["panel_border"],
            **kwargs,
        )
        self._label = ctk.CTkLabel(
            self,
            text       = "⬤  SLEEPING",
            font       = FONT_LABEL,
            text_color = COLORS["muted"],
        )
        self._label.pack(padx=16, pady=8)
        self._blink_job = None

    def set_status(self, status: str) -> None:
        """Update the displayed status. Stops any blink animation."""
        self._stop_blink()
        text, color = self._STATUS_CONFIG.get(
            status, (f"◉  {status.upper()}", COLORS["text"])
        )
        self._label.configure(text=text, text_color=color)
        if status == "listening":
            self._start_blink(color)

    def _start_blink(self, color: str, interval: int = 600) -> None:
        _visible = [True]

        def _toggle():
            if not _visible[0]:
                self._label.configure(text_color=color)
            else:
                self._label.configure(text_color=COLORS["panel"])
            _visible[0] = not _visible[0]
            self._blink_job = self.after(interval, _toggle)

        _toggle()

    def _stop_blink(self) -> None:
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None


# ── Mic button ───────────────────────────────────────────────

class MicButton(ctk.CTkButton):
    """
    Large pulsing microphone button with active/idle states.
    """

    def __init__(self, parent, command: Callable, **kwargs) -> None:
        super().__init__(
            parent,
            text         = "🎤  LISTEN",
            font         = FONT_BUTTON,
            command      = command,
            fg_color     = COLORS["accent_glow"],
            hover_color  = COLORS["accent"],
            text_color   = COLORS["text"],
            corner_radius = 40,
            height        = 52,
            border_width  = 2,
            border_color  = COLORS["accent"],
            **kwargs,
        )
        self._active = False

    def set_active(self, active: bool) -> None:
        """Toggle between active (listening) and idle appearance."""
        self._active = active
        if active:
            self.configure(
                text        = "⏹  STOP",
                fg_color    = COLORS["error"],
                hover_color = "#C0392B",
                border_color = COLORS["error"],
            )
        else:
            self.configure(
                text        = "🎤  LISTEN",
                fg_color    = COLORS["accent_glow"],
                hover_color = COLORS["accent"],
                border_color = COLORS["accent"],
            )


# ── Text command bar ──────────────────────────────────────────

class TextCommandBar(ctk.CTkFrame):
    """
    Keyboard input bar for typing commands directly.
    """

    def __init__(self, parent, on_submit: Callable[[str], None], **kwargs) -> None:
        super().__init__(
            parent,
            fg_color     = COLORS["panel"],
            corner_radius = 8,
            border_width  = 1,
            border_color  = COLORS["panel_border"],
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self._on_submit = on_submit

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text = "Type a command…",
            font             = FONT_INPUT,
            fg_color         = COLORS["bg"],
            border_color     = COLORS["panel_border"],
            text_color       = COLORS["text"],
            corner_radius    = 6,
            height           = 38,
        )
        self._entry.grid(row=0, column=0, padx=(10, 6), pady=8, sticky="ew")
        self._entry.bind("<Return>", self._submit)

        ctk.CTkButton(
            self,
            text         = "→",
            font         = FONT_BUTTON,
            command      = self._submit,
            fg_color     = COLORS["accent_glow"],
            hover_color  = COLORS["accent"],
            text_color   = COLORS["text"],
            corner_radius = 6,
            width        = 42,
            height       = 38,
        ).grid(row=0, column=1, padx=(0, 10), pady=8)

    def _submit(self, event=None) -> None:
        text = self._entry.get().strip()
        if text:
            self._on_submit(text)
            self._entry.delete(0, "end")
