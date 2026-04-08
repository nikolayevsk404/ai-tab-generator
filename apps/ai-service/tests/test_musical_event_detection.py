from app.services.musical_event_detection import _is_probable_harmonic_duplicate


def test_harmonic_duplicate_detection_matches_expected_ratio() -> None:
    assert _is_probable_harmonic_duplicate(880.0, 440.0) is True


def test_non_harmonic_interval_is_not_treated_as_duplicate() -> None:
    assert _is_probable_harmonic_duplicate(523.25, 440.0) is False
