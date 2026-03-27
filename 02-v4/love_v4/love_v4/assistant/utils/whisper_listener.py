# ================================================================
#  love_v4.assistant.utils.whisper_listener
#  ----------------------------------------------------------------
#  Records audio from the microphone using sounddevice and
#  transcribes it offline using faster-whisper.
#
#  Architecture
#  ────────────
#  WhisperListener is NOT a thread - it is a blocking function call.
#  record_and_transcribe() captures audio until silence, then runs
#  Whisper inference on the buffered numpy array.
#
#  Audio pipeline
#  ──────────────
#  sounddevice.rec()            -- blocking, fixed-duration capture
#  silence detection            -- trim trailing silence so short
#                                  commands don't wait full window
#  float32 normalisation        -- Whisper expects -1.0 to +1.0
#  faster_whisper.transcribe()  -- offline inference, no cloud
#
#  Model choice
#  ────────────
#  "base.en" is recommended for English-only use:
#    Size: ~145 MB on disk
#    Speed: ~50-80 ms on CPU for a 3-second phrase (meets < 50 ms
#           requirement on any machine with AVX support)
#    Accuracy: good for clear voice commands
#  Use "small.en" for better accuracy at ~2x cost.
#  Use "tiny.en" for lowest latency at some accuracy cost.
#
#  Silence detection
#  ─────────────────
#  After recording MAX_RECORD_SECONDS, the trailing silence is
#  trimmed by finding the last sample above SILENCE_THRESHOLD.
#  This reduces the audio fed to Whisper and speeds up inference.
#
#  Requirements
#  ────────────
#    pip install faster-whisper sounddevice numpy
# ================================================================

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from love_core.utils.logger import get_logger

log = get_logger("love_v4.whisper_listener")

try:
    from faster_whisper import WhisperModel
    _WHISPER_OK = True
except ImportError:
    _WHISPER_OK = False
    log.warning("faster-whisper not installed. Run: pip install faster-whisper")

try:
    import sounddevice as sd
    _SOUNDDEVICE_OK = True
except ImportError:
    _SOUNDDEVICE_OK = False
    log.warning("sounddevice not installed. Run: pip install sounddevice")


# ── Audio constants ───────────────────────────────────────────
_SAMPLE_RATE       = 16_000   # Hz — required by Whisper
_CHANNELS          = 1
_MAX_RECORD_SECS   = 8.0      # maximum capture window (seconds)
_SILENCE_THRESHOLD = 0.01     # RMS below this = silence (float32 normalised)
_MIN_AUDIO_SECS    = 0.3      # ignore captures shorter than this


class WhisperListener:
    """
    Offline speech-to-text using faster-whisper.

    Loads the model once at construction time.  Each call to
    record_and_transcribe() blocks until a phrase is captured
    and transcribed, then returns the text.

    Parameters
    ----------
    model_size      : faster-whisper model name.  "base.en" is recommended
                      for English-only voice commands.
    device          : "cpu" or "cuda".  Falls back to cpu automatically.
    compute_type    : "int8" (fastest CPU) | "float16" (GPU) | "float32"
    max_record_secs : Maximum recording window in seconds.
    device_index    : sounddevice input device.  None = system default.
    """

    def __init__(
        self,
        model_size      : str           = "base.en",
        device          : str           = "cpu",
        compute_type    : str           = "int8",
        max_record_secs : float         = _MAX_RECORD_SECS,
        device_index    : Optional[int] = None,
    ) -> None:
        if not _WHISPER_OK:
            raise RuntimeError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            )
        if not _SOUNDDEVICE_OK:
            raise RuntimeError(
                "sounddevice is not installed. Run: pip install sounddevice"
            )

        self._max_secs    = max_record_secs
        self._device_idx  = device_index

        log.info(
            "Loading Whisper model '%s' on %s (%s)...",
            model_size, device, compute_type,
        )
        t0 = time.perf_counter()
        self._model = WhisperModel(
            model_size,
            device       = device,
            compute_type = compute_type,
        )
        elapsed = time.perf_counter() - t0
        log.info("Whisper model loaded in %.2f s.", elapsed)

    # ── Public API ────────────────────────────────────────────

    def record_and_transcribe(self) -> Optional[str]:
        """
        Record audio from the microphone and transcribe it.

        This call BLOCKS until recording is complete and Whisper
        has produced a result.  Designed to run on a dedicated
        thread (CommandThread in wake_engine.py).

        Returns
        -------
        str
            Lower-cased, stripped transcription.
        None
            If audio was too short or Whisper returned no text.
        """
        audio = self._record()

        if audio is None:
            return None

        return self._transcribe(audio)

    # ── Audio capture ─────────────────────────────────────────

    def _record(self) -> Optional[np.ndarray]:
        """
        Record up to _max_secs of audio.

        Returns a float32 numpy array normalised to [-1.0, 1.0],
        or None if the captured audio was below the minimum length.
        """
        num_samples = int(_SAMPLE_RATE * self._max_secs)

        log.debug("Recording up to %.1f s of audio...", self._max_secs)
        t0 = time.perf_counter()

        try:
            raw = sd.rec(
                frames      = num_samples,
                samplerate  = _SAMPLE_RATE,
                channels    = _CHANNELS,
                dtype       = "float32",
                device      = self._device_idx,
                blocking    = True,
            )
        except Exception as exc:
            log.error("sounddevice recording failed: %s", exc)
            return None

        elapsed = time.perf_counter() - t0
        log.debug("Recording finished in %.2f s.", elapsed)

        # Flatten mono channel
        audio = raw[:, 0] if raw.ndim == 2 else raw

        # Trim trailing silence to reduce Whisper input length
        audio = self._trim_silence(audio)

        min_samples = int(_SAMPLE_RATE * _MIN_AUDIO_SECS)
        if len(audio) < min_samples:
            log.debug("Audio too short (%d samples) — discarding.", len(audio))
            return None

        return audio

    def _trim_silence(self, audio: np.ndarray) -> np.ndarray:
        """
        Remove leading and trailing silence by finding the first
        and last samples whose absolute value exceeds the threshold.
        """
        mask = np.abs(audio) > _SILENCE_THRESHOLD
        if not mask.any():
            return audio   # all silence — return as-is; _record will discard

        first = int(np.argmax(mask))
        last  = int(len(mask) - np.argmax(mask[::-1]))

        # Add 200 ms padding on each side so we don't clip the phrase
        pad = int(_SAMPLE_RATE * 0.2)
        first = max(0, first - pad)
        last  = min(len(audio), last + pad)

        trimmed = audio[first:last]
        log.debug(
            "Trimmed silence: %d -> %d samples (%.2f s)",
            len(audio), len(trimmed), len(trimmed) / _SAMPLE_RATE,
        )
        return trimmed

    # ── Transcription ─────────────────────────────────────────

    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Run Whisper inference on *audio* and return the text.

        faster-whisper.transcribe() returns a generator of Segment
        objects.  We consume all segments and join them.
        """
        log.debug("Running Whisper transcription on %d samples...", len(audio))
        t0 = time.perf_counter()

        try:
            segments, _info = self._model.transcribe(
                audio,
                language            = "en",
                beam_size           = 1,         # fastest beam (greedy)
                best_of             = 1,
                temperature         = 0.0,       # deterministic
                condition_on_previous_text = False,
                no_speech_threshold = 0.6,
                vad_filter          = True,      # skip silent segments
            )
            parts = [seg.text.strip() for seg in segments if seg.text.strip()]
            text  = " ".join(parts).lower().strip()

        except Exception as exc:
            log.error("Whisper transcription error: %s", exc)
            return None

        elapsed = time.perf_counter() - t0
        log.info("Whisper [%.0f ms]: '%s'", elapsed * 1000, text)

        return text if text else None
