from app.services.fretboard_mapper import infer_technique


def test_infer_technique_is_disabled_for_basic_mode() -> None:
    events = [
        {
            "time": 0.0,
            "harmonic_candidate": False,
            "expression": {
                "bend_candidate": True,
                "release_bend_candidate": False,
                "vibrato_candidate": False,
                "wah_candidate": False,
            },
        }
    ]

    mapped_notes = [{"string": 2, "fret": 15}]

    assert infer_technique(0, events, mapped_notes, []) is None
