from app.agent.audio_to_tab_agent import AudioToTabAgent


def test_agent_transposes_unreachable_notes_without_failing(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.load_audio",
        lambda audio_bytes, filename: ([0.0, 0.1], 22050),
    )
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.run_solo_transcription",
        lambda audio_bytes, filename, signal, sample_rate: {
            "audio_context": {
                "tempo_bpm": 120.0,
                "beat_times": [0.0, 0.5],
                "onset_times": [0.0, 0.12],
                "total_duration": 1.0,
                "guitar_tone": "distorted",
                "meter_numerator": 4,
                "meter_denominator": 4,
                "distortion_features": {
                    "spectral_flatness": 0.03,
                    "zero_crossing_rate": 0.1,
                    "harmonic_ratio": 1.3,
                },
            },
            "embedding": {
                "model": "handcrafted-mir-embedding",
                "dimension": 8,
                "vector": [0.0] * 8,
            },
            "transcription": {
                "backend": "librosa-fallback",
                "events": [
                    {
                        "time": 0.12,
                        "duration": 0.1,
                        "frequencies": [1396.91],
                        "notes": ["F6"],
                        "primary_note": "F6",
                        "is_chord": False,
                        "octave_doubling": False,
                        "octave_pairs": [],
                        "harmonic_candidate": False,
                        "expression": {},
                        "features": {"polyphony": 1},
                    }
                ],
            },
        },
    )

    result = AudioToTabAgent().run(b"fake", "sample.wav")

    assert len(result["tablature"]) == 1
    assert result["audio_context"]["guitar_tone"] == "distorted"
    assert result["audio_context"]["tempo_bpm"] == 120.0
    assert result["audio_context"]["detected_string_count"] == 6
    assert result["audio_context"]["transcription_backend"] == "librosa-fallback"
    assert result["tablature"][0]["note"] == "F6"
    assert result["tablature"][0]["mapped_note"] == "F5"
    assert result["tablature"][0]["transposed"] is True
    assert result["tablature"][0]["time"] == 0.125
    assert result["tablature"][0]["duration"] == 0.125
    assert result["warnings"][0]["reason"] == "note_out_of_range_transposed_by_octave"
    assert result["exports"]["gp5"]["filename"] == "sample.gp5"


def test_agent_preserves_chord_tab_events(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.load_audio",
        lambda audio_bytes, filename: ([0.0, 0.1], 22050),
    )
    monkeypatch.setattr(
        "app.agent.audio_to_tab_agent.run_solo_transcription",
        lambda audio_bytes, filename, signal, sample_rate: {
            "audio_context": {
                "tempo_bpm": 100.0,
                "beat_times": [0.0, 0.6],
                "onset_times": [0.0, 0.3],
                "total_duration": 1.2,
                "guitar_tone": "clean",
                "meter_numerator": 4,
                "meter_denominator": 4,
            },
            "embedding": {
                "model": "handcrafted-mir-embedding",
                "dimension": 8,
                "vector": [0.0] * 8,
            },
            "transcription": {
                "backend": "basic-pitch",
                "events": [
                    {
                        "time": 0.0,
                        "duration": 0.2,
                        "frequencies": [329.63, 246.94],
                        "notes": ["E4", "B3"],
                        "primary_note": "E4",
                        "is_chord": True,
                        "octave_doubling": False,
                        "octave_pairs": [],
                        "harmonic_candidate": False,
                        "expression": {},
                        "features": {"polyphony": 2, "transcription_confidence": 0.92, "candidate_strengths": [0.92]},
                    }
                ],
            },
        },
    )

    result = AudioToTabAgent().run(b"fake", "sample.wav")

    assert result["tab_events"][0]["event_type"] == "chord"
    assert len(result["tab_events"][0]["notes"]) == 2
    assert len(result["tablature"]) == 2
