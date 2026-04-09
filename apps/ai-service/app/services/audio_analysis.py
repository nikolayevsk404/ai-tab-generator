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
    hop_length = 256
    onset_envelope = librosa.onset.onset_strength(y=guitar_signal, sr=sample_rate, hop_length=hop_length)
    tempo_candidates = librosa.feature.tempo(
        onset_envelope=onset_envelope,
        sr=sample_rate,
        hop_length=hop_length,
        aggregate=None,
    )

    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset_envelope, sr=sample_rate, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate, hop_length=hop_length).tolist()
    onset_frames = librosa.onset.onset_detect(
        y=guitar_signal,
        sr=sample_rate,
        hop_length=hop_length,
        backtrack=True,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate, hop_length=hop_length).tolist()
    estimated_tempo = _estimate_tempo(
        beat_times=beat_times,
        onset_times=onset_times,
        tempo_candidates=tempo_candidates,
        onset_envelope=onset_envelope,
        sample_rate=sample_rate,
        hop_length=hop_length,
    )

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


def _estimate_tempo(
    beat_times: list[float],
    onset_times: list[float],
    tempo_candidates: np.ndarray,
    onset_envelope: np.ndarray,
    sample_rate: int,
    hop_length: int,
) -> float:
    weighted_candidates: list[tuple[float, float]] = []

    if len(beat_times) >= 2:
        intervals = np.diff(np.asarray(beat_times, dtype=float))
        valid_intervals = intervals[(intervals > 0.14) & (intervals < 1.6)]
        if valid_intervals.size:
            bpm = 60.0 / float(np.median(valid_intervals))
            weighted_candidates.append((_normalize_bpm(bpm), 1.0))

    if len(onset_times) >= 3:
        onset_intervals = np.diff(np.asarray(onset_times, dtype=float))
        valid_onsets = onset_intervals[(onset_intervals > 0.08) & (onset_intervals < 1.2)]
        if valid_onsets.size:
            # Median over onset spacings helps with tight alternate picking without collapsing to a constant BPM.
            onset_bpm = 60.0 / float(np.median(valid_onsets))
            weighted_candidates.append((_normalize_bpm(onset_bpm), 0.8))

    if tempo_candidates.size:
        finite_candidates = tempo_candidates[np.isfinite(tempo_candidates)]
        if finite_candidates.size:
            weighted_candidates.append((_normalize_bpm(float(np.median(finite_candidates))), 0.75))
            weighted_candidates.append((_normalize_bpm(float(np.percentile(finite_candidates, 65))), 0.6))

    ac_candidate = _tempo_from_onset_autocorrelation(onset_envelope, sample_rate, hop_length)
    if ac_candidate is not None:
        weighted_candidates.append((ac_candidate, 1.1))

    if weighted_candidates:
        return _pick_consensus_bpm(weighted_candidates)

    return 110.0


def _normalize_bpm(bpm: float) -> float:
    while bpm < 60:
        bpm *= 2
    while bpm > 220:
        bpm /= 2
    return bpm


def _tempo_from_onset_autocorrelation(onset_envelope: np.ndarray, sample_rate: int, hop_length: int) -> float | None:
    if onset_envelope.size < 8:
        return None

    centered = onset_envelope - np.mean(onset_envelope)
    autocorrelation = librosa.autocorrelate(centered, max_size=min(len(centered), 4096))
    if autocorrelation.size < 3:
        return None

    tempo_freqs = librosa.tempo_frequencies(len(autocorrelation), sr=sample_rate, hop_length=hop_length)
    valid = np.isfinite(tempo_freqs) & (tempo_freqs >= 60.0) & (tempo_freqs <= 220.0)
    if not np.any(valid):
        return None

    ac_valid = np.copy(autocorrelation)
    ac_valid[~valid] = -np.inf
    best_idx = int(np.argmax(ac_valid))
    best_bpm = float(tempo_freqs[best_idx])
    if not np.isfinite(best_bpm):
        return None
    return _normalize_bpm(best_bpm)


def _pick_consensus_bpm(weighted_candidates: list[tuple[float, float]]) -> float:
    if not weighted_candidates:
        return 110.0

    # Score each BPM by neighborhood support. This avoids collapsing to a single spurious tempo guess.
    support_scores: list[tuple[float, float]] = []
    for bpm, weight in weighted_candidates:
        support = weight
        for other_bpm, other_weight in weighted_candidates:
            delta = abs(other_bpm - bpm)
            if delta <= 3:
                support += other_weight
            elif delta <= 6:
                support += other_weight * 0.5
        support_scores.append((bpm, support))

    support_scores.sort(key=lambda item: item[1], reverse=True)
    top_support = support_scores[0][1]
    top_group = [bpm for bpm, score in support_scores if score >= top_support * 0.92]
    return float(np.median(np.asarray(top_group, dtype=float)))
