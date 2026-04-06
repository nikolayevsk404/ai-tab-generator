from __future__ import annotations

import math

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def frequency_to_note_name(frequency: float) -> str:
    midi_number = round(69 + 12 * math.log2(frequency / 440.0))
    octave = (midi_number // 12) - 1
    note_name = NOTE_NAMES[midi_number % 12]
    return f"{note_name}{octave}"
