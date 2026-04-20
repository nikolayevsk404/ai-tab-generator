from app.services.fretboard_mapper import infer_technique


def test_infer_technique_marks_repicked_same_note() -> None:
    events = [
        {
            "time": 0.0,
            "duration": 0.08,
            "primary_note": "E4",
            "harmonic_candidate": False,
            "expression": {
                "bend_candidate": False,
                "release_bend_candidate": False,
                "vibrato_candidate": False,
                "sustain_candidate": False,
                "wah_candidate": False,
            },
        },
        {
            "time": 0.11,
            "duration": 0.07,
            "primary_note": "E4",
            "harmonic_candidate": False,
            "expression": {
                "bend_candidate": False,
                "release_bend_candidate": False,
                "vibrato_candidate": False,
                "sustain_candidate": False,
                "wah_candidate": False,
            },
        }
    ]

    mapped_notes = [{"string": 2, "fret": 15}]

    assert infer_technique(0, events, mapped_notes, []) == "repalhetada"


def test_infer_technique_marks_sustain_when_note_is_held() -> None:
    events = [
        {
            "time": 0.0,
            "duration": 0.34,
            "primary_note": "G4",
            "harmonic_candidate": False,
            "expression": {
                "bend_candidate": False,
                "release_bend_candidate": False,
                "vibrato_candidate": False,
                "sustain_candidate": True,
                "wah_candidate": False,
            },
        }
    ]

    mapped_notes = [{"string": 1, "fret": 3}]

    assert infer_technique(0, events, mapped_notes, []) == "sustain"
