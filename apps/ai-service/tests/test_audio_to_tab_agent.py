from app.agent.audio_to_tab_agent import AudioToTabAgent


def test_agent_transposes_unreachable_notes_without_failing(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.load_audio",
        lambda audio_bytes, filename: ([0.0, 0.1], 22050),
    )
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.analyze_audio_context",
        lambda signal, sample_rate: {
            "tempo_bpm": 120.0,
            "beat_times": [0.0, 0.5],
            "guitar_tone": "distorted",
            "distortion_features": {
                "spectral_flatness": 0.03,
                "zero_crossing_rate": 0.1,
                "harmonic_ratio": 1.3,
            },
        },
    )
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.detect_pitch_segments",
        lambda audio_bytes, filename, guitar_tone: [{"time": 0.12, "frequency": 1396.91}],
    )

    result = AudioToTabAgent().run(b"fake", "sample.wav")

    assert len(result["tablature"]) == 1
    assert result["audio_context"]["guitar_tone"] == "distorted"
    assert result["audio_context"]["tempo_bpm"] == 120.0
    assert result["tablature"][0]["note"] == "F6"
    assert result["tablature"][0]["mapped_note"] == "F5"
    assert result["tablature"][0]["transposed"] is True
    assert result["tablature"][0]["time"] == 0.125
    assert result["warnings"][0]["reason"] == "note_out_of_range_transposed_by_octave"
    assert result["exports"]["gp5"]["filename"] == "sample.gp5"
