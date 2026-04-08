from __future__ import annotations

import io
from typing import Any

import numpy as np
import soundfile as sf

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


def signal_to_audio_bytes(signal: np.ndarray, sample_rate: int, filename: str) -> bytes:
    buffer = io.BytesIO()
    safe_signal = np.asarray(signal, dtype=np.float32)
    sf.write(buffer, safe_signal, sample_rate, format="WAV")
    buffer.seek(0)
    return buffer.read()


def isolate_guitar_signal(signal: np.ndarray) -> np.ndarray:
    harmonic, percussive = librosa.effects.hpss(signal)
    emphasized = (harmonic * 0.8) + (signal * 0.2)
    peak = float(np.max(np.abs(emphasized))) if emphasized.size else 0.0
    if peak <= 1e-6:
        return emphasized
    return emphasized / peak


def analyze_audio_context(signal: np.ndarray, sample_rate: int) -> dict[str, Any]:
    guitar_signal = isolate_guitar_signal(signal)
    onset_envelope = librosa.onset.onset_strength(y=guitar_signal, sr=sample_rate)
    tempo_candidates = librosa.feature.tempo(
        onset_envelope=onset_envelope,
        sr=sample_rate,
        aggregate=None,
    )

    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset_envelope, sr=sample_rate)
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate).tolist()
    onset_frames = librosa.onset.onset_detect(y=guitar_signal, sr=sample_rate, backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate).tolist()
    estimated_tempo = _estimate_tempo(beat_times, tempo_candidates)

    spectral_flatness = float(np.mean(librosa.feature.spectral_flatness(y=guitar_signal)))
    zero_crossing_rate = float(np.mean(librosa.feature.zero_crossing_rate(y=guitar_signal)))
    harmonic, percussive = librosa.effects.hpss(signal)
    harmonic_energy = float(np.mean(np.abs(harmonic)))
    percussive_energy = float(np.mean(np.abs(percussive)))
    harmonic_ratio = harmonic_energy / (percussive_energy + 1e-6)
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=guitar_signal, sr=sample_rate)))
    guitar_presence_score = _estimate_guitar_presence_score(
        spectral_flatness=spectral_flatness,
        zero_crossing_rate=zero_crossing_rate,
        harmonic_ratio=harmonic_ratio,
        rolloff=rolloff,
    )

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
        "onset_times": [round(float(time), 3) for time in onset_times[:256]],
        "total_duration": round(float(len(signal) / sample_rate), 3),
        "guitar_tone": guitar_tone,
        "distortion_features": {
            "spectral_flatness": round(spectral_flatness, 5),
            "zero_crossing_rate": round(zero_crossing_rate, 5),
            "harmonic_ratio": round(harmonic_ratio, 5),
            "spectral_rolloff": round(rolloff, 2),
        },
        "guitar_presence_score": round(guitar_presence_score, 3),
    }


def _estimate_guitar_presence_score(
    spectral_flatness: float,
    zero_crossing_rate: float,
    harmonic_ratio: float,
    rolloff: float,
) -> float:
    score = 0.0
    if harmonic_ratio >= 1.3:
        score += 0.35
    if 0.005 <= spectral_flatness <= 0.12:
        score += 0.2
    if 0.02 <= zero_crossing_rate <= 0.18:
        score += 0.2
    if 1200 <= rolloff <= 6500:
        score += 0.25
    return min(1.0, score)


def _estimate_tempo(beat_times: list[float], tempo_candidates: np.ndarray) -> float:
    candidate_bpms: list[float] = []

    if len(beat_times) >= 2:
        intervals = np.diff(np.asarray(beat_times, dtype=float))
        valid_intervals = intervals[(intervals > 0.18) & (intervals < 1.5)]
        if valid_intervals.size:
            bpm = 60.0 / float(np.median(valid_intervals))
            candidate_bpms.append(_normalize_bpm(bpm))

    if tempo_candidates.size:
        finite_candidates = tempo_candidates[np.isfinite(tempo_candidates)]
        if finite_candidates.size:
            candidate_bpms.append(_normalize_bpm(float(np.median(finite_candidates))))
            candidate_bpms.append(_normalize_bpm(float(np.percentile(finite_candidates, 65))))

    if candidate_bpms:
        candidate_bpms.sort()
        return float(np.median(np.asarray(candidate_bpms, dtype=float)))

    return 120.0


def _normalize_bpm(bpm: float) -> float:
    while bpm < 70:
        bpm *= 2
    while bpm > 190:
        bpm /= 2
    return bpm
