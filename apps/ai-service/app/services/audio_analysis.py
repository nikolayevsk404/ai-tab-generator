from __future__ import annotations

import io
from typing import Any

import numpy as np

try:
    import librosa
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "librosa is required to run the AI service. Install the dependencies from requirements.txt."
    ) from exc


def load_audio(audio_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
    suffix = filename.split(".")[-1].lower()
    if suffix not in {"wav", "mp3"}:
        raise ValueError("Only .wav and .mp3 files are supported.")

    buffer = io.BytesIO(audio_bytes)
    signal, sample_rate = librosa.load(buffer, sr=22050, mono=True)

    if signal.size == 0:
        raise ValueError("The provided audio file is empty.")

    return signal, sample_rate


def analyze_audio_context(signal: np.ndarray, sample_rate: int) -> dict[str, Any]:
    onset_envelope = librosa.onset.onset_strength(y=signal, sr=sample_rate)
    tempo_array = librosa.feature.tempo(onset_envelope=onset_envelope, sr=sample_rate, aggregate=None)
    estimated_tempo = float(np.median(tempo_array)) if tempo_array.size else 120.0

    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset_envelope, sr=sample_rate)
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate).tolist()

    spectral_flatness = float(np.mean(librosa.feature.spectral_flatness(y=signal)))
    zero_crossing_rate = float(np.mean(librosa.feature.zero_crossing_rate(y=signal)))
    harmonic, percussive = librosa.effects.hpss(signal)
    harmonic_energy = float(np.mean(np.abs(harmonic)))
    percussive_energy = float(np.mean(np.abs(percussive)))
    harmonic_ratio = harmonic_energy / (percussive_energy + 1e-6)

    distorted_score = 0
    if spectral_flatness > 0.02:
        distorted_score += 1
    if zero_crossing_rate > 0.08:
        distorted_score += 1
    if harmonic_ratio < 2.5:
        distorted_score += 1

    if distorted_score >= 3:
        guitar_tone = "distorted"
    elif distorted_score == 2:
        guitar_tone = "mixed"
    else:
        guitar_tone = "clean"

    return {
        "tempo_bpm": round(estimated_tempo, 2),
        "beat_times": [round(float(time), 3) for time in beat_times[:128]],
        "guitar_tone": guitar_tone,
        "distortion_features": {
            "spectral_flatness": round(spectral_flatness, 5),
            "zero_crossing_rate": round(zero_crossing_rate, 5),
            "harmonic_ratio": round(harmonic_ratio, 5),
        },
    }
