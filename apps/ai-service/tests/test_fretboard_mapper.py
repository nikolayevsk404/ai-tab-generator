from app.services.fretboard_mapper import DEFAULT_PROFILE, map_note_to_fretboard, map_note_to_fretboard_with_fallback


def test_map_note_to_fretboard_prefers_open_string() -> None:
    assert map_note_to_fretboard("E2") == {"string": 6, "fret": 0}


def test_map_note_to_fretboard_with_fallback_transposes_by_octave() -> None:
    assert map_note_to_fretboard_with_fallback("F6", DEFAULT_PROFILE, previous_average_fret=5.0) == {
        "string": 1,
        "fret": 13,
        "mapped_note": "F5",
        "transposed": True,
    }
