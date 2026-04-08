from __future__ import annotations

from app.services.audio_analysis import load_audio
from app.services.fretboard_mapper import infer_fretboard_profile, map_events_to_fretboard
from app.services.gp5_exporter import export_tablature_to_gp5
from app.services.timing_grid import build_time_grid, quantize_events_to_grid
from app.services.transcription_stack import run_solo_transcription


class AudioToTabAgent:
    def run(self, audio_bytes: bytes, filename: str, job_id: str | None = None) -> dict:
        signal, sample_rate = load_audio(audio_bytes, filename)
        transcription_result = run_solo_transcription(
            audio_bytes=audio_bytes,
            filename=filename,
            signal=signal,
            sample_rate=sample_rate,
        )
        audio_context = transcription_result["audio_context"]
        events = transcription_result["transcription"]["events"]
        timing_grid = build_time_grid(
            audio_context.get("beat_times", []),
            audio_context.get("total_duration", 0.0),
            audio_context["tempo_bpm"],
            audio_context["guitar_tone"],
            meter_numerator=int(audio_context.get("meter_numerator", 4) or 4),
            meter_denominator=int(audio_context.get("meter_denominator", 4) or 4),
        )
        events = quantize_events_to_grid(events, timing_grid)
        events = [event for event in events if event.get("notes")]

        fretboard_profile = infer_fretboard_profile(events)
        tab_events, tablature, warnings = map_events_to_fretboard(events, fretboard_profile)

        return {
            "job_id": job_id,
            "filename": filename,
            "audio_context": {
                **audio_context,
                "embedding_model": transcription_result["embedding"]["model"],
                "embedding_dimension": transcription_result["embedding"]["dimension"],
                "transcription_backend": transcription_result["transcription"]["backend"],
                "raw_note_event_count": transcription_result["transcription"].get("raw_note_event_count", len(events)),
                "post_filter_event_count": len(events),
                "timing_grid": timing_grid,
                "detected_string_count": fretboard_profile.string_count,
                "detected_tuning": fretboard_profile.name,
                "tuning_notes": fretboard_profile.tuning,
            },
            "embedding": transcription_result["embedding"],
            "detected_frequencies": [
                {
                    "time": event["time"],
                    "frequencies": event["frequencies"],
                }
                for event in events
            ],
            "detected_notes": [
                {
                    "time": event["time"],
                    "duration": event["duration"],
                    "notes": event["notes"],
                    "primary_note": event["primary_note"],
                    "is_chord": event["is_chord"],
                    "octave_doubling": event["octave_doubling"],
                    "harmonic_candidate": event["harmonic_candidate"],
                    "expression": event.get("expression", {}),
                }
                for event in events
            ],
            "tablature": tablature,
            "tab_events": tab_events,
            "segments": events,
            "warnings": warnings,
            "exports": {
                "gp5": export_tablature_to_gp5(
                    tab_events,
                    filename,
                    tempo=int(round(audio_context["tempo_bpm"])),
                    tuning=fretboard_profile.tuning,
                    timing_grid=timing_grid,
                ),
            },
        }
