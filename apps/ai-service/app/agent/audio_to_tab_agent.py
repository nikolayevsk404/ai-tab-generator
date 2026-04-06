from __future__ import annotations

from app.services.audio_analysis import analyze_audio_context, load_audio
from app.services.fretboard_mapper import map_note_to_fretboard_with_fallback
from app.services.gp5_exporter import export_tablature_to_gp5
from app.services.note_mapper import frequency_to_note_name
from app.services.pitch_detection import detect_pitch_segments


class AudioToTabAgent:
    def run(self, audio_bytes: bytes, filename: str, job_id: str | None = None) -> dict:
        signal, sample_rate = load_audio(audio_bytes, filename)
        audio_context = analyze_audio_context(signal, sample_rate)
        segments = detect_pitch_segments(
            audio_bytes=audio_bytes,
            filename=filename,
            guitar_tone=audio_context["guitar_tone"],
        )

        detected_notes = []
        tablature = []
        warnings = []

        for segment in segments:
            note_name = frequency_to_note_name(segment["frequency"])
            position = map_note_to_fretboard_with_fallback(note_name)
            quantized_time = quantize_time(
                segment["time"],
                audio_context["tempo_bpm"],
                audio_context["guitar_tone"],
            )

            detected_note = {
                "time": segment["time"],
                "quantized_time": quantized_time,
                "note": note_name,
                "frequency": segment["frequency"],
            }

            if position.get("transposed"):
                detected_note["mapped_note"] = position["mapped_note"]
                detected_note["transposed"] = True
                warnings.append(
                    {
                        "time": segment["time"],
                        "note": note_name,
                        "mapped_note": position["mapped_note"],
                        "reason": "note_out_of_range_transposed_by_octave",
                    }
                )

            if position.get("unmapped"):
                detected_note["unmapped"] = True
                warnings.append(
                    {
                        "time": segment["time"],
                        "note": note_name,
                        "reason": "note_out_of_range_skipped",
                    }
                )
                detected_notes.append(detected_note)
                continue

            detected_notes.append(detected_note)

            tablature.append(
                {
                    "time": quantized_time,
                    "detected_time": segment["time"],
                    "note": note_name,
                    "mapped_note": position["mapped_note"],
                    "string": position["string"],
                    "fret": position["fret"],
                    "transposed": bool(position.get("transposed")),
                }
            )

        return {
            "job_id": job_id,
            "filename": filename,
            "audio_context": audio_context,
            "detected_frequencies": segments,
            "detected_notes": detected_notes,
            "tablature": tablature,
            "segments": segments,
            "warnings": warnings,
            "exports": {
                "gp5": export_tablature_to_gp5(tablature, filename, tempo=int(round(audio_context["tempo_bpm"]))),
            },
        }


def quantize_time(time_seconds: float, tempo_bpm: float, guitar_tone: str) -> float:
    if tempo_bpm <= 0:
        return round(time_seconds, 3)

    beat_duration = 60 / tempo_bpm
    subdivision = 4 if guitar_tone in {"distorted", "mixed"} else 2
    grid = beat_duration / subdivision

    if grid <= 0:
        return round(time_seconds, 3)

    return round(round(time_seconds / grid) * grid, 3)
