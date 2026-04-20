from app.services.transcription_stack import (
    _enforce_monophonic_timeline,
    _refine_events_with_onsets,
    _stabilize_pitch_contour,
)


def test_refine_events_with_onsets_snaps_and_shortens_long_event() -> None:
    refined = _refine_events_with_onsets(
        [
            {
                "time": 0.12,
                "duration": 0.33,
                "primary_note": "A3",
                "notes": ["A3"],
                "expression": {"sustain_candidate": True},
                "features": {"transcription_confidence": 0.8, "candidate_strengths": [0.8]},
            }
        ],
        [0.1, 0.28, 0.5],
        "distorted",
    )

    assert refined[0]["time"] == 0.1
    assert refined[0]["duration"] == 0.18


def test_enforce_monophonic_timeline_shifts_late_overlap_instead_of_dropping() -> None:
    kept = _enforce_monophonic_timeline(
        [
            {
                "time": 0.0,
                "duration": 0.2,
                "primary_note": "A3",
                "expression": {"sustain_candidate": True},
                "features": {"transcription_confidence": 0.91, "candidate_strengths": [0.91]},
            },
            {
                "time": 0.16,
                "duration": 0.12,
                "primary_note": "B3",
                "expression": {"sustain_candidate": False},
                "features": {"transcription_confidence": 0.72, "candidate_strengths": [0.72]},
            },
        ]
    )

    assert len(kept) == 2
    assert kept[1]["time"] == 0.2
    assert kept[1]["duration"] == 0.08


def test_stabilize_pitch_contour_corrects_isolated_octave_error() -> None:
    stabilized = _stabilize_pitch_contour(
        [
            {
                "primary_note": "A3",
                "notes": ["A3"],
                "frequencies": [220.0],
                "is_chord": False,
                "features": {"transcription_confidence": 0.61},
            },
            {
                "primary_note": "A5",
                "notes": ["A5"],
                "frequencies": [880.0],
                "is_chord": False,
                "features": {"transcription_confidence": 0.58},
            },
            {
                "primary_note": "B3",
                "notes": ["B3"],
                "frequencies": [246.94],
                "is_chord": False,
                "features": {"transcription_confidence": 0.74},
            },
        ]
    )

    assert stabilized[1]["primary_note"] == "A4"
    assert stabilized[1]["features"]["octave_stabilized"] is True
