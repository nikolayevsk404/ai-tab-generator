from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.note_mapper import midi_to_note_name, note_name_to_midi

TUNING_PROFILES = [
    {"name": "6-string standard", "string_count": 6, "notes": ["E4", "B3", "G3", "D3", "A2", "E2"]},
    {"name": "6-string drop d", "string_count": 6, "notes": ["E4", "B3", "G3", "D3", "A2", "D2"]},
    {"name": "7-string standard", "string_count": 7, "notes": ["E4", "B3", "G3", "D3", "A2", "E2", "B1"]},
]


@dataclass
class FretboardProfile:
    name: str
    string_count: int
    tuning: dict[int, str]


DEFAULT_PROFILE = FretboardProfile(
    name="6-string standard",
    string_count=6,
    tuning={1: "E4", 2: "B3", 3: "G3", 4: "D3", 5: "A2", 6: "E2"},
)


def infer_fretboard_profile(events: list[dict[str, Any]]) -> FretboardProfile:
    return DEFAULT_PROFILE


def score_fretboard_profile(events: list[dict[str, Any]], profile: FretboardProfile) -> float:
    total_score = 0.0
    previous_average_fret = 5.0

    for event in events:
        mapped_notes = []

        for note_name in event["notes"]:
            candidates = find_fretboard_positions(note_name, profile)
            if not candidates:
                total_score += 50
                continue

            best_candidate = min(candidates, key=lambda candidate: (abs(candidate["fret"] - previous_average_fret), candidate["fret"]))
            mapped_notes.append(best_candidate)
            total_score += best_candidate["fret"] * 0.15

        if mapped_notes:
            average_fret = sum(candidate["fret"] for candidate in mapped_notes) / len(mapped_notes)
            total_score += abs(average_fret - previous_average_fret) * 0.2
            previous_average_fret = average_fret

        if event["is_chord"]:
            total_score -= len(mapped_notes) * 0.1

    return total_score


def map_events_to_fretboard(events: list[dict[str, Any]], profile: FretboardProfile) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tab_events: list[dict[str, Any]] = []
    flattened_tablature: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    previous_average_fret = 5.0

    for event_index, event in enumerate(events):
        mapped_notes = []
        used_strings: set[int] = set()

        for note_name in event["notes"]:
            resolution = map_note_to_fretboard_with_fallback(note_name, profile, previous_average_fret, used_strings)

            if resolution.get("unmapped"):
                warnings.append(
                    {
                        "time": event["time"],
                        "note": note_name,
                        "reason": "note_out_of_range_skipped",
                    }
                )
                continue

            if resolution.get("transposed"):
                warnings.append(
                    {
                        "time": event["time"],
                        "note": note_name,
                        "mapped_note": resolution["mapped_note"],
                        "reason": "note_out_of_range_transposed_by_octave",
                    }
                )

            used_strings.add(int(resolution["string"]))
            mapped_notes.append(
                {
                    "note": note_name,
                    "mapped_note": resolution["mapped_note"],
                    "string": int(resolution["string"]),
                    "fret": int(resolution["fret"]),
                    "transposed": bool(resolution.get("transposed")),
                }
            )

        if not mapped_notes:
            continue

        average_fret = sum(note["fret"] for note in mapped_notes) / len(mapped_notes)
        previous_average_fret = average_fret

        primary_note = mapped_notes[0]
        mapped_notes = [primary_note]
        event_type = "single_note"
        technique = infer_technique(event_index, events, mapped_notes, tab_events)

        tab_event = {
            "event_id": event_index,
            "time": event["time"],
            "duration": event["duration"],
            "detected_time": event.get("detected_time", event["time"]),
            "detected_duration": event.get("detected_duration", event["duration"]),
            "grid_start_index": event.get("grid_start_index"),
            "grid_end_index": event.get("grid_end_index"),
            "event_type": event_type,
            "technique": technique,
            "notes": mapped_notes,
            "source_notes": [event["primary_note"]],
            "features": event["features"],
            "octave_doubling": False,
            "harmonic_candidate": event["harmonic_candidate"],
        }
        tab_events.append(tab_event)

        for mapped_note in mapped_notes:
            flattened_tablature.append(
                {
                    "event_id": event_index,
                    "time": event["time"],
                    "detected_time": event.get("detected_time", event["time"]),
                    "duration": event["duration"],
                    "detected_duration": event.get("detected_duration", event["duration"]),
                    "event_type": event_type,
                    "technique": technique,
                    "note": mapped_note["note"],
                    "mapped_note": mapped_note["mapped_note"],
                    "string": mapped_note["string"],
                    "fret": mapped_note["fret"],
                    "transposed": mapped_note["transposed"],
                }
            )

    return tab_events, flattened_tablature, warnings


def find_fretboard_positions(note_name: str, profile: FretboardProfile) -> list[dict[str, int]]:
    target_midi = note_name_to_midi(note_name)
    candidates: list[dict[str, int]] = []

    for string_number, open_note in profile.tuning.items():
        fret = target_midi - note_name_to_midi(open_note)
        if 0 <= fret <= 24:
            candidates.append({"string": string_number, "fret": fret})

    return sorted(candidates, key=lambda position: (position["fret"], abs(position["string"] - 4)))


def map_note_to_fretboard_with_fallback(
    note_name: str,
    profile: FretboardProfile,
    previous_average_fret: float,
    used_strings: set[int] | None = None,
) -> dict[str, Any]:
    used_strings = used_strings or set()
    direct_position = select_best_position(find_fretboard_positions(note_name, profile), previous_average_fret, used_strings)
    if direct_position is not None:
        return {
            "string": direct_position["string"],
            "fret": direct_position["fret"],
            "mapped_note": note_name,
            "transposed": False,
        }

    target_midi = note_name_to_midi(note_name)

    for semitones in (12, -12, 24, -24):
        candidate_note = midi_to_note_name(target_midi + semitones)
        fallback_position = select_best_position(find_fretboard_positions(candidate_note, profile), previous_average_fret, used_strings)

        if fallback_position is not None:
            return {
                "string": fallback_position["string"],
                "fret": fallback_position["fret"],
                "mapped_note": candidate_note,
                "transposed": True,
            }

    return {
        "mapped_note": note_name,
        "transposed": False,
        "unmapped": True,
    }


def select_best_position(
    candidates: list[dict[str, int]],
    previous_average_fret: float,
    used_strings: set[int],
) -> dict[str, int] | None:
    available = [candidate for candidate in candidates if candidate["string"] not in used_strings]
    pool = available or candidates

    if not pool:
        return None

    return min(
        pool,
        key=lambda candidate: (abs(candidate["fret"] - previous_average_fret), candidate["fret"], candidate["string"]),
    )


def infer_technique(
    event_index: int,
    events: list[dict[str, Any]],
    mapped_notes: list[dict[str, Any]],
    previous_tab_events: list[dict[str, Any]],
) -> str | None:
    # Keep the first iteration intentionally simple: focus on pitch/time accuracy only.
    return None


def map_note_to_fretboard(note_name: str) -> dict[str, int]:
    positions = find_fretboard_positions(note_name, DEFAULT_PROFILE)

    if not positions:
        raise ValueError(f"Could not map note {note_name} to the 6-string fretboard.")

    return positions[0]
