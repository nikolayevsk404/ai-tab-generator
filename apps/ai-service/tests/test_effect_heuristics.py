from app.services.fretboard_mapper import infer_technique


def test_infer_technique_prefers_bend_expression() -> None:
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

    assert infer_technique(0, events, mapped_notes, []) == "bend"


def test_infer_technique_prefers_wah_over_generic_single_note() -> None:
    events = [
        {
            "time": 0.0,
            "harmonic_candidate": False,
            "expression": {
                "bend_candidate": False,
                "release_bend_candidate": False,
                "vibrato_candidate": False,
                "wah_candidate": True,
            },
        }
    ]

    mapped_notes = [{"string": 3, "fret": 7}]

    assert infer_technique(0, events, mapped_notes, []) == "wah"
