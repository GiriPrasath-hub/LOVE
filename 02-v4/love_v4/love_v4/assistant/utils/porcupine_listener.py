# ================================================================
#  love_v4.assistant.utils.porcupine_listener
#  ----------------------------------------------------------------
#  Wraps pvporcupine + sounddevice into a single, self-contained
#  class that reads one audio frame at a time and signals whenever
#  the keyword "hey love" is detected.
#
#  Architecture
#  ────────────
#  PorcupineListener is NOT a thread - it is a pure audio processor.
#  The threading model lives in wake_engine.py (separation of concerns).
#  The caller controls the loop so the engine can be paused or stopped
#  at any point without race conditions.
#
#  Latency budget
#  ────────────────────────────────────────────
#  Porcupine processes one 512-sample frame at 16 000 Hz:
#    512 / 16000 = 32 ms per frame
#  sounddevice read:       ~1-2 ms
#  Porcupine inference:    ~1-3 ms  (native C library)
#  Total hot-path:         < 35 ms  (requirement: < 30 ms per frame)
#  ────────────────────────────────────────────
#
#  Audio stream
#  ────────────
#  sounddevice.RawInputStream is opened once at start() and kept
#  open for the entire session.  Re-opening on every frame would
#  add 5+ ms of latency per cycle.
#
#  Requirements
#  ────────────
#    pip install pvporcupine sounddevice numpy
#    A free Picovoice access key from console.picovoice.ai
#    A .ppn keyword file trained for "hey love"
# ================================================================

from __future__ import annotations

import os
from typing import Optional

import numpy as np

from love_core.utils.logger import get_logger

log = get_logger("love_v4.porcupine_listener")

try:
    import pvporcupine
    _PORCUPINE_OK = True
except ImportError:
    _PORCUPINE_OK = False
    log.warning("pvporcupine not installed. Run: pip install pvporcupine")

try:
    import sounddevice as sd
    _SOUNDDEVICE_OK = True
except ImportError:
    _SOUNDDEVICE_OK = False
    log.warning("sounddevice not installed. Run: pip install sounddevice")


class PorcupineListener:
    """
    Hardware-accelerated keyword spotter using Picovoice Porcupine.

    Parameters
    ----------
    access_key      : Picovoice access key (free tier at console.picovoice.ai)
    keyword_path    : Path to .ppn keyword file. If absent, falls back to
                      builtin_keyword.
    builtin_keyword : Built-in keyword name used when keyword_path is missing.
                      Available built-ins: "porcupine", "hey google", etc.
    sensitivity     : 0.0-1.0. Higher = more detections, more false positives.
    device_index    : sounddevice input device index. None = system default.
    """

    def __init__(
        self,
        access_key      : str,
        keyword_path    : Optional[str] = None,
        builtin_keyword : str           = "porcupine",
        sensitivity     : float         = 0.5,
        device_index    : Optional[int] = None,
    ) -> None:
        if not _PORCUPINE_OK:
            raise RuntimeError("pvporcupine is not installed. Run: pip install pvporcupine")
        if not _SOUNDDEVICE_OK:
            raise RuntimeError("sounddevice is not installed. Run: pip install sounddevice")

        self._access_key   = access_key
        self._keyword_path = keyword_path
        self._builtin      = builtin_keyword
        self._sensitivity  = float(sensitivity)
        self._device_index = device_index

        self._porcupine: Optional[object] = None
        self._stream: Optional[object]    = None
        self._running = False

        log.debug(
            "PorcupineListener created (keyword=%s sensitivity=%.2f)",
            keyword_path or builtin_keyword, sensitivity,
        )

    # ── Lifecycle ────────────────────────────────────────────

    def start(self) -> None:
        """
        Initialise the Porcupine engine and open the audio stream.
        Must be called before any call to process_frame().
        """
        if self._running:
            return

        try:
            if self._keyword_path and os.path.isfile(self._keyword_path):
                self._porcupine = pvporcupine.create(
                    access_key    = self._access_key,
                    keyword_paths = [self._keyword_path],
                    sensitivities = [self._sensitivity],
                )
                log.info("Porcupine: loaded keyword file '%s'", self._keyword_path)
            else:
                if self._keyword_path:
                    log.warning(
                        "Keyword file not found at '%s'. Falling back to built-in '%s'.",
                        self._keyword_path, self._builtin,
                    )
                self._porcupine = pvporcupine.create(
                    access_key    = self._access_key,
                    keywords      = [self._builtin],
                    sensitivities = [self._sensitivity],
                )
                log.info("Porcupine: loaded built-in keyword '%s'", self._builtin)

        except pvporcupine.PorcupineActivationError as exc:
            raise RuntimeError(
                f"Invalid Picovoice access key. Get a free key at "
                f"https://console.picovoice.ai/  Error: {exc}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Porcupine init failed: {exc}") from exc

        # Porcupine requires exactly: 16 000 Hz, 512 samples/frame, int16, mono
        self._stream = sd.RawInputStream(
            samplerate = self._porcupine.sample_rate,
            blocksize  = self._porcupine.frame_length,
            dtype      = "int16",
            channels   = 1,
            device     = self._device_index,
        )
        self._stream.start()
        self._running = True

        log.info(
            "PorcupineListener started (sample_rate=%d frame_length=%d)",
            self._porcupine.sample_rate, self._porcupine.frame_length,
        )

    def stop(self) -> None:
        """Close the audio stream and release the Porcupine engine."""
        self._running = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as exc:
                log.debug("Stream close error (non-fatal): %s", exc)
            self._stream = None

        if self._porcupine is not None:
            try:
                self._porcupine.delete()
            except Exception as exc:
                log.debug("Porcupine delete error (non-fatal): %s", exc)
            self._porcupine = None

        log.info("PorcupineListener stopped.")

    # ── Frame processing ─────────────────────────────────────

    def process_frame(self) -> bool:
        """
        Read exactly one audio frame and run Porcupine inference.

        Returns
        -------
        True   : keyword detected in this frame
        False  : no keyword (the common case — runs ~30 ms per call)

        Raises
        ------
        RuntimeError : if called before start()
        """
        if not self._running or self._stream is None or self._porcupine is None:
            raise RuntimeError("PorcupineListener not started. Call start() first.")

        # read() returns (bytes_buffer, overflow_flag)
        raw, _ = self._stream.read(self._porcupine.frame_length)
        pcm    = np.frombuffer(raw, dtype=np.int16)

        # process() returns keyword index (>= 0) or -1 (no match)
        result   = self._porcupine.process(pcm)
        detected = result >= 0

        if detected:
            log.debug("Porcupine: keyword index %d matched", result)

        return detected

    # ── Properties ───────────────────────────────────────────

    @property
    def sample_rate(self) -> int:
        if self._porcupine is None:
            raise RuntimeError("Call start() first.")
        return self._porcupine.sample_rate

    @property
    def frame_length(self) -> int:
        if self._porcupine is None:
            raise RuntimeError("Call start() first.")
        return self._porcupine.frame_length

    @property
    def is_running(self) -> bool:
        return self._running
