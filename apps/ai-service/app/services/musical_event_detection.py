from __future__ import annotations

from typing import Any

import numpy as np

from app.services.audio_analysis import load_audio
from app.services.note_mapper import frequency_to_note_name, note_name_to_midi

try:
    import librosa
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "librosa is required to run the AI service. Install the dependencies from requirements.txt."
    ) from exc


def detect_musical_events(
    audio_bytes: bytes,
    filename: str,
    guitar_tone: str,
    onset_times: list[float] | None = None,
) -> list[dict[str, Any]]:
    signal, sample_rate = load_audio(audio_bytes, filename)

    detected_onsets = onset_times or _detect_onsets(signal, sample_rate, guitar_tone)
    if not detected_onsets:
        detected_onsets = [0.0]

    signal_duration = len(signal) / sample_rate
    boundaries = detected_onsets + [signal_duration]
    events: list[dict[str, Any]] = []

    for index, start_time in enumerate(detected_onsets):
        end_time = boundaries[index + 1]
        if end_time <= start_time:
            continue

        start_sample = max(0, int(start_time * sample_rate))
        end_sample = min(len(signal), int(end_time * sample_rate))
        window = signal[start_sample:end_sample]

        minimum_window_length = _minimum_pitch_window_length(sample_rate)
        if len(window) < max(256, minimum_window_length // 2):
            continue

        primary = _estimate_primary_frequency(window, sample_rate, guitar_tone)
        if primary is None:
            continue
        note_name = frequency_to_note_name(float(primary))
        midi_note = note_name_to_midi(note_name)
        if midi_note < 40 or midi_note > 88:
            continue
        note_names = [note_name]
        analysis_n_fft = _resolve_n_fft(len(window), guitar_tone)
        analysis_window = _prepare_window_for_spectral_analysis(window, analysis_n_fft)
        analysis_hop_length = max(64, analysis_n_fft // 4)
        expression = {
            "bend_candidate": False,
            "release_bend_candidate": False,
            "vibrato_candidate": False,
            "sustain_candidate": (end_time - start_time) >= 0.18,
            "wah_candidate": False,
        }
        spectral_centroid = float(
            np.mean(
                librosa.feature.spectral_centroid(
                    y=analysis_window,
                    sr=sample_rate,
                    n_fft=analysis_n_fft,
                    hop_length=analysis_hop_length,
                )
            )
        )
        rms = float(np.mean(librosa.feature.rms(y=analysis_window, frame_length=analysis_n_fft, hop_length=analysis_hop_length)))

        events.append(
            {
                "time": round(float(start_time), 3),
                "duration": round(float(end_time - start_time), 3),
                "frequencies": [round(float(primary), 2)],
                "notes": note_names,
                "primary_note": note_names[0],
                "is_chord": False,
                "octave_doubling": False,
                "octave_pairs": [],
                "harmonic_candidate": spectral_centroid > 2200 and rms < 0.12,
                "expression": expression,
                "features": {
                    "spectral_centroid": round(spectral_centroid, 2),
                    "rms": round(rms, 5),
                    "polyphony": 1,
                    "candidate_strengths": [1.0],
                },
            }
        )

    return _post_process_events(events, signal_duration)


def _estimate_primary_frequency(window: np.ndarray, sample_rate: int, guitar_tone: str) -> float | None:
    frame_length = max(_minimum_pitch_window_length(sample_rate), _resolve_n_fft(len(window), guitar_tone))
    analysis_window = _prepare_window_for_pitch_analysis(window, frame_length)
    hop_length = max(64, frame_length // 4)
    fmin = librosa.note_to_hz("E2")
    fmax = librosa.note_to_hz("E6")

    try:
        pyin_f0, voiced_flag, voiced_prob = librosa.pyin(
            analysis_window,
            fmin=fmin,
            fmax=fmax,
            sr=sample_rate,
            frame_length=frame_length,
            hop_length=hop_length,
        )
        if pyin_f0 is not None:
            finite = np.isfinite(pyin_f0)
            if finite.any():
                voiced = finite
                if voiced_flag is not None:
                    voiced &= voiced_flag
                if voiced_prob is not None:
                    voiced &= voiced_prob >= 0.45
                tracked = pyin_f0[voiced]
                if tracked.size:
                    return float(np.median(tracked))
    except Exception:
        pass

    try:
        yin_curve = librosa.yin(
            analysis_window,
            fmin=fmin,
            fmax=fmax,
            sr=sample_rate,
            frame_length=frame_length,
            hop_length=hop_length,
        )
        valid = yin_curve[np.isfinite(yin_curve)]
        if valid.size:
            return float(np.median(valid))
    except Exception:
        pass

    candidates = _extract_note_candidates(window, sample_rate, guitar_tone)
    if not candidates:
        return None
    return float(candidates[0]["frequency"])


def _detect_onsets(signal: np.ndarray, sample_rate: int, guitar_tone: str) -> list[float]:
    hop_length = 256 if guitar_tone in {"distorted", "mixed"} else 512
    if guitar_tone in {"distorted", "mixed"}:
        pre_max = 10
        post_max = 10
        pre_avg = 40
        post_avg = 40
        wait = 2
        delta = 0.09
    else:
        pre_max = 16
        post_max = 16
        pre_avg = 70
        post_avg = 70
        wait = 3
        delta = 0.13

    onset_frames = librosa.onset.onset_detect(
        y=signal,
        sr=sample_rate,
        hop_length=hop_length,
        backtrack=True,
        pre_max=pre_max,
        post_max=post_max,
        pre_avg=pre_avg,
        post_avg=post_avg,
        delta=delta,
        wait=wait,
    )
    return [round(float(time), 3) for time in librosa.frames_to_time(onset_frames, sr=sample_rate, hop_length=hop_length)]


def _extract_note_candidates(window: np.ndarray, sample_rate: int, guitar_tone: str) -> list[dict[str, float | str]]:
    n_fft = _resolve_n_fft(len(window), guitar_tone)
    hop_length = max(64, n_fft // 4)
    analysis_window = _prepare_window_for_spectral_analysis(window, n_fft)
    pitches, magnitudes = librosa.piptrack(y=analysis_window, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)

    candidate_rows: list[tuple[float, float]] = []

    for pitch_row, magnitude_row in zip(pitches, magnitudes):
        active = magnitude_row > np.percentile(magnitude_row, 92)
        for frequency, magnitude in zip(pitch_row[active], magnitude_row[active]):
            if not np.isfinite(frequency):
                continue
            if frequency < 50 or frequency > 1800:
                continue
            candidate_rows.append((float(frequency), float(magnitude)))

    if not candidate_rows:
        return []

    candidate_rows.sort(key=lambda item: item[1], reverse=True)

    unique_candidates: list[dict[str, float | str]] = []
    used_midis: list[int] = []

    for frequency, magnitude in candidate_rows:
        note_name = frequency_to_note_name(frequency)
        midi_note = note_name_to_midi(note_name)

        if any(abs(midi_note - used_midi) <= 1 for used_midi in used_midis):
            continue

        if any(_is_probable_harmonic_duplicate(frequency, existing["frequency"]) for existing in unique_candidates):
            continue

        unique_candidates.append(
            {
                "frequency": round(frequency, 2),
                "note": note_name,
                "magnitude": round(magnitude, 5),
            }
        )
        used_midis.append(midi_note)

        if len(unique_candidates) >= 6:
            break

    return unique_candidates


def _select_primary_candidate(
    candidates: list[dict[str, float | str]],
    guitar_tone: str,
) -> dict[str, float | str] | None:
    if not candidates:
        return None

    strongest = float(candidates[0]["magnitude"])

    ranked = sorted(
        candidates,
        key=lambda candidate: _candidate_priority(candidate, strongest, guitar_tone),
    )

    return ranked[0]


def _resolve_n_fft(window_length: int, guitar_tone: str) -> int:
    preferred = 4096 if guitar_tone != "clean" else 2048

    if window_length <= 512:
        return 512

    n_fft = min(preferred, window_length)
    power_of_two = 2 ** int(np.floor(np.log2(n_fft)))
    return max(512, power_of_two)


def _minimum_pitch_window_length(sample_rate: int) -> int:
    fmin = librosa.note_to_hz("E2")
    required_length = int(np.ceil((sample_rate / fmin) * 2.1))
    return max(512, 2 ** int(np.ceil(np.log2(required_length))))


def _prepare_window_for_pitch_analysis(window: np.ndarray, frame_length: int) -> np.ndarray:
    if len(window) >= frame_length:
        return window

    return librosa.util.fix_length(window, size=frame_length)


def _prepare_window_for_spectral_analysis(window: np.ndarray, n_fft: int) -> np.ndarray:
    if len(window) >= n_fft:
        return window

    return librosa.util.fix_length(window, size=n_fft)


def _is_probable_harmonic_duplicate(current_frequency: float, reference_frequency: float) -> bool:
    ratio = max(current_frequency, reference_frequency) / max(min(current_frequency, reference_frequency), 1e-6)
    return any(abs(ratio - multiplier) < 0.08 for multiplier in (2.0, 3.0, 4.0))


def _candidate_priority(
    candidate: dict[str, float | str],
    strongest: float,
    guitar_tone: str,
) -> tuple[float, float, float]:
    frequency = float(candidate["frequency"])
    magnitude = float(candidate["magnitude"])
    ratio = magnitude / max(strongest, 1e-6)
    midi_note = note_name_to_midi(str(candidate["note"]))

    high_register_penalty = 0.08 if guitar_tone == "distorted" and frequency > 950 else 0.0
    ultra_high_penalty = 0.12 if frequency > 1320 else 0.0
    score = -(ratio - high_register_penalty - ultra_high_penalty)

    return (score, midi_note, -magnitude)


def _detect_expression_features(
    window: np.ndarray,
    sample_rate: int,
    guitar_tone: str,
    n_fft: int,
    hop_length: int,
) -> dict[str, Any]:
    frame_length = max(1024, n_fft)
    rms_curve = librosa.feature.rms(
        y=window,
        frame_length=frame_length,
        hop_length=hop_length,
    )[0]

    try:
        pitch_curve = librosa.yin(
            window,
            fmin=librosa.note_to_hz("E2"),
            fmax=librosa.note_to_hz("E6"),
            sr=sample_rate,
            frame_length=frame_length,
            hop_length=hop_length,
        )
    except Exception:
        pitch_curve = np.array([])

    active_mask = np.ones_like(pitch_curve, dtype=bool)
    if len(rms_curve) and len(pitch_curve):
        rms_threshold = max(float(np.max(rms_curve)) * 0.35, 1e-5)
        active_mask = rms_curve[: len(pitch_curve)] >= rms_threshold

    finite_mask = np.isfinite(pitch_curve) if len(pitch_curve) else np.array([], dtype=bool)
    analysis_mask = finite_mask & active_mask[: len(finite_mask)] if finite_mask.size else np.array([], dtype=bool)
    finite_pitches = pitch_curve[analysis_mask] if analysis_mask.size else np.array([])

    if finite_pitches.size >= 3:
        midi_curve = 69 + 12 * np.log2(finite_pitches / 440.0)
        centered_curve = midi_curve - np.median(midi_curve)
        pitch_span = float(np.max(midi_curve) - np.min(midi_curve))
        pitch_std = float(np.std(midi_curve))
        pitch_diff = np.diff(midi_curve) if len(midi_curve) > 1 else np.array([])
        positive_motion = float(np.sum(np.clip(pitch_diff, 0, None)))
        negative_motion = float(np.sum(np.clip(-pitch_diff, 0, None)))
        end_start_delta = float(midi_curve[-1] - midi_curve[0])
        stable_ratio = float(np.mean(np.abs(centered_curve) <= 0.18))
        sign_changes = int(np.sum(np.diff(np.signbit(centered_curve)) != 0)) if len(centered_curve) > 2 else 0
        tail_size = max(2, len(midi_curve) // 3)
        tail_curve = midi_curve[-tail_size:]
        tail_stability = float(np.std(tail_curve)) if len(tail_curve) else 0.0
    else:
        pitch_span = 0.0
        pitch_std = 0.0
        positive_motion = 0.0
        negative_motion = 0.0
        end_start_delta = 0.0
        stable_ratio = 1.0
        sign_changes = 0
        tail_stability = 0.0

    centroid_curve = librosa.feature.spectral_centroid(
        y=window,
        sr=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
    )[0]
    bandwidth_curve = librosa.feature.spectral_bandwidth(
        y=window,
        sr=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
    )[0]

    centroid_std = float(np.std(centroid_curve)) if len(centroid_curve) else 0.0
    bandwidth_std = float(np.std(bandwidth_curve)) if len(bandwidth_curve) else 0.0
    centroid_span = float(np.max(centroid_curve) - np.min(centroid_curve)) if len(centroid_curve) else 0.0

    is_sustained = (
        len(finite_pitches) >= 3
        and pitch_span <= 0.55
        and pitch_std <= 0.16
        and stable_ratio >= 0.72
    )
    is_bend = (
        not is_sustained
        and pitch_span >= 1.0
        and end_start_delta >= 0.85
        and positive_motion > negative_motion * 1.6
        and tail_stability <= 0.3
    )
    is_release_bend = (
        not is_sustained
        and pitch_span >= 1.0
        and end_start_delta <= -0.85
        and negative_motion > positive_motion * 1.6
        and tail_stability <= 0.3
    )
    is_vibrato = (
        not is_sustained
        and not is_bend
        and not is_release_bend
        and 0.22 <= pitch_std <= 0.9
        and 0.35 <= pitch_span <= 2.2
        and len(finite_pitches) >= 5
        and sign_changes >= 3
        and stable_ratio <= 0.58
    )
    is_wah = (
        centroid_span >= (900 if guitar_tone != "clean" else 700)
        and centroid_std >= (260 if guitar_tone != "clean" else 180)
        and bandwidth_std >= 180
    )

    return {
        "bend_candidate": is_bend,
        "release_bend_candidate": is_release_bend,
        "vibrato_candidate": is_vibrato,
        "sustain_candidate": is_sustained,
        "wah_candidate": is_wah,
        "pitch_span_semitones": round(pitch_span, 3),
        "pitch_std_semitones": round(pitch_std, 3),
        "end_start_delta_semitones": round(end_start_delta, 3),
        "stable_ratio": round(stable_ratio, 3),
        "sign_changes": sign_changes,
        "centroid_span": round(centroid_span, 2),
        "centroid_std": round(centroid_std, 2),
    }


def _post_process_events(events: list[dict[str, Any]], signal_duration: float) -> list[dict[str, Any]]:
    if not events:
        return []

    cleaned_events: list[dict[str, Any]] = []
    min_duration = max(0.035, signal_duration / 2000)

    for event in sorted(events, key=lambda item: item["time"]):
        if event["duration"] < min_duration:
            continue

        if cleaned_events:
            previous = cleaned_events[-1]
            if _should_merge_neighbor_events(previous, event):
                previous_end = previous["time"] + previous["duration"]
                current_end = event["time"] + event["duration"]
                previous["duration"] = round(max(previous_end, current_end) - previous["time"], 3)
                continue

        cleaned_events.append(event)

    return cleaned_events


def _should_merge_neighbor_events(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    if previous["primary_note"] != current["primary_note"]:
        return False

    prev_start = float(previous["time"])
    prev_duration = float(previous["duration"])
    cur_start = float(current["time"])
    cur_duration = float(current["duration"])
    prev_end = prev_start + prev_duration
    gap = cur_start - prev_end

    # Keep fast repeated picks as separate notes; merge only near-duplicates.
    near_duplicate_start = abs(cur_start - prev_start) <= 0.015
    very_similar_duration = abs(cur_duration - prev_duration) <= 0.025
    slight_overlap = gap <= 0.01
    return near_duplicate_start and very_similar_duration and slight_overlap
