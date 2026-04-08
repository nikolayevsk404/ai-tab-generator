from __future__ import annotations

import math

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def frequency_to_note_name(frequency: float) -> str:
    return midi_to_note_name(round(69 + 12 * math.log2(frequency / 440.0)))


def midi_to_note_name(midi_number: int) -> str:
    octave = (midi_number // 12) - 1
    note_name = NOTE_NAMES[midi_number % 12]
    return f"{note_name}{octave}"


def note_name_to_midi(note_name: str) -> int:
    if len(note_name) == 2:
        pitch_class = note_name[0]
        octave = int(note_name[1])
    else:
        pitch_class = note_name[:2]
        octave = int(note_name[2])

    return (octave + 1) * 12 + NOTE_NAMES.index(pitch_class)
