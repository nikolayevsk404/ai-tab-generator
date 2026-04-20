from app.services.timing_grid import build_time_grid, quantize_events_to_grid
from app.services.audio_analysis import _pick_consensus_bpm
from app.services.transcription_stack import _should_merge_same_note_events


def test_build_time_grid_uses_sixteenth_grid_for_distorted_audio() -> None:
    grid = build_time_grid([0.0, 0.5, 1.0], 1.2, 120.0, "distorted")

    assert grid["subdivisions_per_beat"] == 4
    assert grid["grid_times"][:5] == [0.0, 0.125, 0.25, 0.375, 0.5]


def test_quantize_events_to_grid_preserves_timeline_progression() -> None:
    grid = build_time_grid([0.0, 0.5, 1.0], 1.2, 120.0, "distorted")
    events = [{"time": 0.12, "duration": 0.09, "notes": ["E2"]}]

    quantized = quantize_events_to_grid(events, grid)

    assert quantized[0]["time"] == 0.125
    assert quantized[0]["duration"] == 0.125


def test_quantize_events_to_grid_reduces_artificial_gap_between_close_notes() -> None:
    grid = build_time_grid([0.0, 0.5, 1.0], 1.2, 120.0, "distorted")
    events = [
        {"time": 0.12, "duration": 0.09, "notes": ["E4"]},
        {"time": 0.23, "duration": 0.08, "notes": ["F4"]},
    ]

    quantized = quantize_events_to_grid(events, grid)

    assert quantized[0]["grid_end_index"] == quantized[1]["grid_start_index"]


def test_pick_consensus_bpm_prefers_clustered_tempo() -> None:
    bpm = _pick_consensus_bpm([(96.2, 1.0), (95.8, 0.9), (192.0, 0.4), (97.1, 0.7)])
    assert 95.0 <= bpm <= 98.0


def test_basic_pitch_dedupe_keeps_fast_repeated_notes() -> None:
    previous = {"time": 0.200, "duration": 0.060}
    current = {"time": 0.270, "duration": 0.055}
    assert _should_merge_same_note_events(previous, current) is False
