from app.services.fretboard_mapper import (
    DEFAULT_PROFILE,
    map_events_to_fretboard,
    map_note_to_fretboard,
    map_note_to_fretboard_with_fallback,
)


def test_map_note_to_fretboard_prefers_open_string() -> None:
    assert map_note_to_fretboard("E2") == {"string": 6, "fret": 0}


def test_map_note_to_fretboard_with_fallback_transposes_by_octave() -> None:
    assert map_note_to_fretboard_with_fallback("F6", DEFAULT_PROFILE, previous_average_fret=5.0) == {
        "string": 1,
        "fret": 13,
        "mapped_note": "F5",
        "transposed": True,
    }


def test_map_events_to_fretboard_keeps_double_stop_events() -> None:
    tab_events, tablature, warnings = map_events_to_fretboard(
        [
            {
                "time": 0.0,
                "duration": 0.25,
                "notes": ["E4", "B3"],
                "primary_note": "E4",
                "is_chord": True,
                "octave_doubling": False,
                "harmonic_candidate": False,
                "features": {"polyphony": 2},
            }
        ],
        DEFAULT_PROFILE,
    )

    assert warnings == []
    assert tab_events[0]["event_type"] == "chord"
    assert len(tab_events[0]["notes"]) == 2
    assert len(tablature) == 2
