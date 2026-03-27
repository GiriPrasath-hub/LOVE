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

import os
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
_MAX_RECORD_SECS   = 5.0      # maximum capture window — keeps Whisper input short
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
            # All physical cores for inference; cuts latency ~800ms -> ~200ms
            cpu_threads  = os.cpu_count() or 4,
            num_workers  = 1,
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
        Stream audio from the microphone using sounddevice.RawInputStream.

        Uses a callback-driven stream instead of sd.rec() so frames
        are captured as they arrive rather than blocking for a fixed
        duration.  The stream stops when:
          - trailing silence exceeds _SILENCE_HOLD_SECS, OR
          - total recording exceeds _max_secs

        Returns a float32 numpy array normalised to [-1.0, 1.0],
        or None if the captured audio was below the minimum length.
        """
        # Each block is 1024 samples (~64 ms at 16 kHz) — small enough for
        # responsive silence detection, large enough to avoid buffer churn.
        _BLOCK_SIZE       = 1024
        _SILENCE_HOLD_SECS = 0.8   # stop after this many seconds of silence
        _SILENCE_BLOCKS    = int(_SILENCE_HOLD_SECS * _SAMPLE_RATE / _BLOCK_SIZE)

        chunks: list[np.ndarray] = []
        silent_blocks = 0
        max_blocks    = int(self._max_secs * _SAMPLE_RATE / _BLOCK_SIZE)

        log.debug("Recording (stream) up to %.1f s...", self._max_secs)
        t0 = time.perf_counter()

        try:
            with sd.RawInputStream(
                samplerate = _SAMPLE_RATE,
                blocksize  = _BLOCK_SIZE,
                dtype      = "int16",
                channels   = _CHANNELS,
                device     = self._device_idx,
            ) as stream:
                for _ in range(max_blocks):
                    if not chunks and silent_blocks > 0:
                        silent_blocks = 0   # reset pre-speech silence counter

                    raw, _ = stream.read(_BLOCK_SIZE)
                    block  = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

                    chunks.append(block)

                    # Detect silence: RMS of this block vs threshold
                    rms = float(np.sqrt(np.mean(block ** 2)))
                    if rms < _SILENCE_THRESHOLD:
                        silent_blocks += 1
                    else:
                        silent_blocks = 0

                    # Stop early once speech has started and silence held
                    if len(chunks) > 3 and silent_blocks >= _SILENCE_BLOCKS:
                        log.debug("Silence hold reached — stopping early.")
                        break

        except Exception as exc:
            log.error("sounddevice stream error: %s", exc)
            return None

        elapsed = time.perf_counter() - t0
        log.debug("Recording finished in %.2f s (%d blocks).", elapsed, len(chunks))

        if not chunks:
            return None

        audio = np.concatenate(chunks)

        min_samples = int(_SAMPLE_RATE * _MIN_AUDIO_SECS)
        if len(audio) < min_samples:
            log.debug("Audio too short (%d samples) — discarding.", len(audio))
            return None

        return audio

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
                language                   = "en",
                beam_size                  = 1,    # greedy — fastest
                best_of                    = 1,
                temperature                = 0.0,  # deterministic
                condition_on_previous_text = False,
                no_speech_threshold        = 0.6,
                # vad_filter removed — requires webrtcvad C extension;
                # silence is handled in _record() via RMS threshold.
            )
            parts = [seg.text.strip() for seg in segments if seg.text.strip()]
            text  = " ".join(parts).lower().strip()

        except Exception as exc:
            log.error("Whisper transcription error: %s", exc)
            return None

        elapsed = time.perf_counter() - t0
        log.info("Whisper [%.0f ms]: '%s'", elapsed * 1000, text)

        return text if text else None
