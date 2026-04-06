from app.agent.audio_to_tab_agent import quantize_time


def test_quantize_time_uses_sixteenth_grid_for_distorted_audio() -> None:
    assert quantize_time(0.12, 120.0, "distorted") == 0.125


def test_quantize_time_uses_eighth_grid_for_clean_audio() -> None:
    assert quantize_time(0.18, 120.0, "clean") == 0.25
