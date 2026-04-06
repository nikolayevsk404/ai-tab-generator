from app.services.note_mapper import frequency_to_note_name


def test_frequency_to_note_name() -> None:
    assert frequency_to_note_name(440.0) == "A4"
