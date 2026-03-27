# ============================================================
#  LOVE v3 — Configuration
#  All constants, paths, and tunable settings live here.
# ============================================================

# ── Wake / Stop words ───────────────────────────────────────
WAKE_WORD  = "hey love"
STOP_WORD  = "bye love"

# ── Speech recognition ──────────────────────────────────────
RECOGNIZER_ENERGY_THRESHOLD = 300       # mic sensitivity
RECOGNIZER_PAUSE_THRESHOLD  = 0.8       # seconds of silence = end of phrase
RECOGNIZER_LANGUAGE         = "en-US"

# ── Text-to-speech ──────────────────────────────────────────
TTS_RATE   = 175        # words per minute
TTS_VOLUME = 1.0        # 0.0 – 1.0

# ── Browser ─────────────────────────────────────────────────
BROWSER_TAB_DELAY = 0.4   # seconds to wait after Ctrl+T before navigating

# ── URLs ────────────────────────────────────────────────────
URLS = {
    "google":   "https://www.google.com",
    "youtube":  "https://www.youtube.com",
    "github":   "https://www.github.com",
    "gmail":    "https://mail.google.com",
    "maps":     "https://maps.google.com",
    "reddit":   "https://www.reddit.com",
    "wikipedia":"https://www.wikipedia.org",
}

# ── Application paths (Windows defaults) ────────────────────
APP_PATHS = {
    "notepad":         "notepad.exe",
    "calculator":      "calc.exe",
    "paint":           "mspaint.exe",
    "file explorer":   "explorer.exe",
    "task manager":    "taskmgr.exe",
    "vs code":         r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "chrome":          r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":         r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "word":            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":           r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
}
