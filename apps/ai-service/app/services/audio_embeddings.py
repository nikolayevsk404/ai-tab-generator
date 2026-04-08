from __future__ import annotations

from typing import Any

import numpy as np

try:
    import librosa
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "librosa is required to run the AI service. Install the dependencies from requirements.txt."
    ) from exc


def compute_audio_embedding(signal: np.ndarray, sample_rate: int) -> dict[str, Any]:
    openl3_embedding = _compute_openl3_embedding(signal, sample_rate)
    if openl3_embedding is not None:
        return openl3_embedding

    fallback_vector = _compute_handcrafted_embedding(signal, sample_rate)
    return {
        "model": "handcrafted-mir-embedding",
        "source": "fallback",
        "dimension": len(fallback_vector),
        "vector": fallback_vector,
    }


def _compute_openl3_embedding(signal: np.ndarray, sample_rate: int) -> dict[str, Any] | None:
    try:
        import torchopenl3  # type: ignore
    except ImportError:
        return None

    try:
        embeddings, _timestamps = torchopenl3.get_audio_embedding(
            signal,
            sample_rate,
            input_repr="mel256",
            content_type="music",
            embedding_size=512,
        )
    except Exception:
        return None

    if embeddings is None or len(embeddings) == 0:
        return None

    pooled = np.mean(embeddings, axis=0)
    return {
        "model": "torchopenl3",
        "source": "pretrained",
        "dimension": int(len(pooled)),
        "vector": pooled.astype(float).round(6).tolist(),
    }


def _compute_handcrafted_embedding(signal: np.ndarray, sample_rate: int) -> list[float]:
    mfcc = librosa.feature.mfcc(y=signal, sr=sample_rate, n_mfcc=13)
    chroma = librosa.feature.chroma_cqt(y=signal, sr=sample_rate)
    spectral_centroid = librosa.feature.spectral_centroid(y=signal, sr=sample_rate)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y=signal)
    rms = librosa.feature.rms(y=signal)

    features = [
        np.mean(mfcc, axis=1),
        np.std(mfcc, axis=1),
        np.mean(chroma, axis=1),
        np.std(chroma, axis=1),
        np.array(
            [
                float(np.mean(spectral_centroid)),
                float(np.std(spectral_centroid)),
                float(np.mean(zero_crossing_rate)),
                float(np.std(zero_crossing_rate)),
                float(np.mean(rms)),
                float(np.std(rms)),
            ]
        ),
    ]

    embedding = np.concatenate(features)
    return embedding.astype(float).round(6).tolist()
