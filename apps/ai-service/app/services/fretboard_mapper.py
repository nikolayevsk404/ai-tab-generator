from __future__ import annotations

NOTE_INDEX = {
    "C": 0,
    "C#": 1,
    "D": 2,
    "D#": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "G#": 8,
    "A": 9,
    "A#": 10,
    "B": 11,
}

TUNING = {
    7: "B1",
    6: "E2",
    5: "A2",
    4: "D3",
    3: "G3",
    2: "B3",
    1: "E4",
}


def note_to_midi(note_name: str) -> int:
    if len(note_name) == 2:
        pitch_class = note_name[0]
        octave = int(note_name[1])
    else:
        pitch_class = note_name[:2]
        octave = int(note_name[2])

    return (octave + 1) * 12 + NOTE_INDEX[pitch_class]


def midi_to_note_name(midi_note: int) -> str:
    octave = (midi_note // 12) - 1
    pitch_class = next(name for name, index in NOTE_INDEX.items() if index == midi_note % 12)
    return f"{pitch_class}{octave}"


def find_fretboard_position(note_name: str) -> dict[str, int] | None:
    target_midi = note_to_midi(note_name)
    candidates: list[dict[str, int]] = []

    for string_number, open_note in TUNING.items():
        fret = target_midi - note_to_midi(open_note)

        if 0 <= fret <= 24:
            candidates.append({"string": string_number, "fret": fret})

    if not candidates:
        return None

    candidates.sort(key=lambda position: (position["fret"], abs(position["string"] - 4)))
    return candidates[0]


def map_note_to_fretboard(note_name: str) -> dict[str, int]:
    position = find_fretboard_position(note_name)

    if position is None:
        raise ValueError(f"Could not map note {note_name} to the 7-string fretboard.")

    return position


def map_note_to_fretboard_with_fallback(note_name: str) -> dict[str, int | str | bool]:
    direct_position = find_fretboard_position(note_name)
    if direct_position is not None:
        return {
            "string": direct_position["string"],
            "fret": direct_position["fret"],
            "mapped_note": note_name,
            "transposed": False,
        }

    target_midi = note_to_midi(note_name)

    for semitones in (12, 24, -12, -24):
        candidate_midi = target_midi + semitones
        candidate_note = midi_to_note_name(candidate_midi)
        fallback_position = find_fretboard_position(candidate_note)

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
