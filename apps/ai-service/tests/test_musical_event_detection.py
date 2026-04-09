from app.services.musical_event_detection import _is_probable_harmonic_duplicate, _should_merge_neighbor_events


def test_harmonic_duplicate_detection_matches_expected_ratio() -> None:
    assert _is_probable_harmonic_duplicate(880.0, 440.0) is True


def test_non_harmonic_interval_is_not_treated_as_duplicate() -> None:
    assert _is_probable_harmonic_duplicate(523.25, 440.0) is False


def test_should_not_merge_fast_repeated_same_note() -> None:
    previous = {"time": 0.100, "duration": 0.050, "primary_note": "E4"}
    current = {"time": 0.160, "duration": 0.045, "primary_note": "E4"}
    assert _should_merge_neighbor_events(previous, current) is False


def test_should_merge_near_duplicate_same_note() -> None:
    previous = {"time": 0.100, "duration": 0.080, "primary_note": "E4"}
    current = {"time": 0.106, "duration": 0.084, "primary_note": "E4"}
    assert _should_merge_neighbor_events(previous, current) is True
