from __future__ import annotations

from typing import Any

import numpy as np

from app.services.audio_analysis import load_audio

try:
    import librosa
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "librosa is required to run the AI service. Install the dependencies from requirements.txt."
    ) from exc


def detect_pitch_segments(
    audio_bytes: bytes,
    filename: str,
    guitar_tone: str = "mixed",
) -> list[dict[str, Any]]:
    signal, sample_rate = load_audio(audio_bytes, filename)

    frame_length = 4096 if guitar_tone == "distorted" else 2048
    hop_length = 256 if guitar_tone == "distorted" else 512

    pitches = librosa.yin(
        signal,
        fmin=librosa.note_to_hz("B1"),
        fmax=librosa.note_to_hz("E6"),
        sr=sample_rate,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    times = librosa.times_like(pitches, sr=sample_rate, hop_length=hop_length)

    segments: list[dict[str, Any]] = []
    dedupe_threshold = 4 if guitar_tone == "distorted" else 2

    for index, frequency in enumerate(pitches):
        if not np.isfinite(frequency):
            continue
        if frequency < 50 or frequency > 1400:
            continue

        rounded_frequency = round(float(frequency), 2)

        if segments and abs(segments[-1]["frequency"] - rounded_frequency) < dedupe_threshold:
            continue

        segments.append(
            {
                "time": round(float(times[index]), 3),
                "frequency": rounded_frequency,
            }
        )

    return segments[:64]
