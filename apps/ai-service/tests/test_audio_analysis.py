from app.services.timing_grid import build_time_grid, quantize_events_to_grid


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
