from __future__ import annotations

import tempfile
from typing import Any

import numpy as np

from app.services.audio_analysis import analyze_audio_context, isolate_guitar_signal, signal_to_audio_bytes
from app.services.audio_embeddings import compute_audio_embedding
from app.services.musical_event_detection import detect_musical_events

try:
    import librosa
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "librosa is required to run the AI service. Install the dependencies from requirements.txt."
    ) from exc


def run_solo_transcription(
    audio_bytes: bytes,
    filename: str,
    signal: np.ndarray,
    sample_rate: int,
) -> dict[str, Any]:
    guitar_signal = isolate_guitar_signal(signal)
    audio_context = analyze_audio_context(signal, sample_rate)
    embedding = compute_audio_embedding(guitar_signal, sample_rate)
    isolated_audio_bytes = signal_to_audio_bytes(guitar_signal, sample_rate, filename)

    backend_result = _transcribe_with_basic_pitch(isolated_audio_bytes, filename)
    if backend_result is None:
        events = detect_musical_events(
            audio_bytes=isolated_audio_bytes,
            filename=filename,
            guitar_tone=audio_context["guitar_tone"],
            onset_times=audio_context.get("onset_times"),
        )
        events = _filter_guitar_events(events, guitar_signal, sample_rate, audio_context["guitar_tone"])
        transcription = {
            "backend": "librosa-fallback",
            "source": "heuristic",
            "events": events,
            "raw_note_event_count": len(events),
        }
    else:
        raw_event_count = len(backend_result["note_events"])
        events = _convert_basic_pitch_events(backend_result["note_events"])
        events = _filter_guitar_events(events, guitar_signal, sample_rate, audio_context["guitar_tone"])
        transcription = {
            "backend": "basic-pitch",
            "source": "pretrained",
            "events": events,
            "raw_note_event_count": raw_event_count,
        }

    meter = _estimate_meter(audio_context)

    return {
        "audio_context": {
            **audio_context,
            "meter_numerator": meter["numerator"],
            "meter_denominator": meter["denominator"],
        },
        "embedding": embedding,
        "transcription": transcription,
    }


def _transcribe_with_basic_pitch(audio_bytes: bytes, filename: str) -> dict[str, Any] | None:
    try:
        from basic_pitch.inference import predict  # type: ignore
    except ImportError:
        return None

    suffix = f".{filename.split('.')[-1].lower()}" if "." in filename else ".wav"

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            model_output, midi_data, note_events = predict(tmp_file.name)
    except Exception:
        return None

    return {
        "model_output": model_output,
        "midi_data": midi_data,
        "note_events": note_events,
    }


def _convert_basic_pitch_events(note_events: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for raw_event in note_events:
        if len(raw_event) < 4:
            continue

        start_time = float(raw_event[0])
        end_time = float(raw_event[1])
        midi_note = int(raw_event[2])
        confidence = float(raw_event[3])
        note_name = _midi_to_note_name(midi_note)

        if end_time <= start_time or confidence < 0.45:
            continue

        expression = {
            "bend_candidate": False,
            "release_bend_candidate": False,
            "vibrato_candidate": False,
            "sustain_candidate": end_time - start_time >= 0.2,
            "wah_candidate": False,
        }

        events.append(
            {
                "time": round(start_time, 3),
                "duration": round(end_time - start_time, 3),
                "frequencies": [round(float(_midi_to_frequency(midi_note)), 2)],
                "notes": [note_name],
                "primary_note": note_name,
                "is_chord": False,
                "octave_doubling": False,
                "octave_pairs": [],
                "harmonic_candidate": False,
                "expression": expression,
                "features": {
                    "polyphony": 1,
                    "candidate_strengths": [round(confidence, 5)],
                    "transcription_confidence": round(confidence, 5),
                },
            }
        )

    return _dedupe_basic_pitch_events(events)


def _estimate_meter(audio_context: dict[str, Any]) -> dict[str, int]:
    try:
        from madmom.features.downbeats import RNNDownBeatProcessor, DBNDownBeatTrackingProcessor  # type: ignore
    except ImportError:
        return {"numerator": 4, "denominator": 4}

    beat_times = audio_context.get("beat_times", [])
    if len(beat_times) < 4:
        return {"numerator": 4, "denominator": 4}

    return {"numerator": 4, "denominator": 4}


def _midi_to_frequency(midi_note: int) -> float:
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def _midi_to_note_name(midi_note: int) -> str:
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"


def _dedupe_basic_pitch_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not events:
        return []

    deduped: list[dict[str, Any]] = []

    for event in sorted(events, key=lambda item: (item["time"], item["primary_note"])):
        if event["duration"] < 0.035:
            continue

        if deduped:
            previous = deduped[-1]
            same_note = previous["primary_note"] == event["primary_note"]
            overlap = event["time"] <= previous["time"] + previous["duration"] + 0.04

            if same_note and overlap:
                previous_end = previous["time"] + previous["duration"]
                current_end = event["time"] + event["duration"]
                previous["duration"] = round(max(previous_end, current_end) - previous["time"], 3)

                previous_confidence = previous["features"]["transcription_confidence"]
                current_confidence = event["features"]["transcription_confidence"]
                merged_confidence = round(max(previous_confidence, current_confidence), 5)
                previous["features"]["transcription_confidence"] = merged_confidence
                previous["features"]["candidate_strengths"] = [merged_confidence]
                previous["expression"]["sustain_candidate"] = previous["duration"] >= 0.2
                continue

        deduped.append(event)

    return deduped


def _filter_guitar_events(
    events: list[dict[str, Any]],
    signal: np.ndarray,
    sample_rate: int,
    guitar_tone: str,
) -> list[dict[str, Any]]:
    filtered_events: list[dict[str, Any]] = []

    for event in events:
        score = _score_event_as_guitar(event, signal, sample_rate, guitar_tone)
        if score < (0.52 if guitar_tone == "clean" else 0.48):
            continue

        event["features"]["guitar_likelihood"] = round(score, 4)
        filtered_events.append(event)

    return filtered_events


def _score_event_as_guitar(
    event: dict[str, Any],
    signal: np.ndarray,
    sample_rate: int,
    guitar_tone: str,
) -> float:
    start_sample = max(0, int(float(event["time"]) * sample_rate))
    end_sample = min(len(signal), int((float(event["time"]) + float(event["duration"])) * sample_rate))
    window = signal[start_sample:end_sample]

    if len(window) < 256:
        return 0.0

    n_fft = 2048 if len(window) >= 2048 else 2 ** int(np.floor(np.log2(len(window))))
    n_fft = max(256, n_fft)
    hop_length = max(64, n_fft // 4)

    rms = float(np.mean(librosa.feature.rms(y=window, frame_length=n_fft, hop_length=hop_length)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=window)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=window)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=window, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=window, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)))

    harmonic, percussive = librosa.effects.hpss(window)
    harmonic_ratio = float(np.mean(np.abs(harmonic))) / (float(np.mean(np.abs(percussive))) + 1e-6)
    confidence = float(event["features"].get("transcription_confidence", event["features"]["candidate_strengths"][0]))

    score = 0.0
    if rms >= 0.008:
        score += 0.2
    if harmonic_ratio >= (1.15 if guitar_tone == "distorted" else 1.35):
        score += 0.25
    if 0.003 <= flatness <= (0.18 if guitar_tone == "distorted" else 0.1):
        score += 0.15
    if 0.015 <= zcr <= 0.2:
        score += 0.1
    if 500 <= centroid <= 5000:
        score += 0.15
    if 1200 <= rolloff <= 8000:
        score += 0.05
    if confidence >= 0.6:
        score += 0.1

    return min(1.0, score)
