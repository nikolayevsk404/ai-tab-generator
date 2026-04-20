from __future__ import annotations

from typing import Any


def build_time_grid(
    beat_times: list[float],
    total_duration: float,
    tempo_bpm: float,
    guitar_tone: str,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
) -> dict[str, Any]:
    beat_count = len(beat_times)
    estimated_beat_duration = 60 / tempo_bpm if tempo_bpm > 0 else 0.5
    onset_density = beat_count / max(total_duration, 1e-6)

    subdivisions_per_beat = 4 if guitar_tone in {"distorted", "mixed"} else 2
    if tempo_bpm >= 132 or onset_density >= 2.4:
        subdivisions_per_beat = 8
    elif tempo_bpm >= 96 or onset_density >= 1.4:
        subdivisions_per_beat = max(subdivisions_per_beat, 4)

    fallback_beat_duration = 60 / tempo_bpm if tempo_bpm > 0 else 0.5
    grid_times: list[float] = []

    normalized_beats = [float(time) for time in beat_times if 0 <= time < total_duration]
    if not normalized_beats or normalized_beats[0] > 0.02:
        normalized_beats = [0.0, *normalized_beats]

    if len(normalized_beats) >= 2:
        for index, beat_time in enumerate(normalized_beats):
            next_beat_time = normalized_beats[index + 1] if index + 1 < len(normalized_beats) else min(total_duration, beat_time + fallback_beat_duration)
            interval = max(next_beat_time - beat_time, fallback_beat_duration / 2)
            step = interval / subdivisions_per_beat

            for subdivision in range(subdivisions_per_beat):
                grid_point = beat_time + (subdivision * step)
                if grid_point < total_duration:
                    grid_times.append(round(grid_point, 4))
    else:
        step = fallback_beat_duration / subdivisions_per_beat
        cursor = 0.0
        while cursor < total_duration + (step / 2):
            grid_times.append(round(cursor, 4))
            cursor += step

    deduped_grid = []
    for time in sorted(set(grid_times)):
        if not deduped_grid or abs(time - deduped_grid[-1]) > 0.005:
            deduped_grid.append(time)

    return {
        "grid_times": deduped_grid,
        "subdivisions_per_beat": subdivisions_per_beat,
        "step_duration": round(_median_step(deduped_grid, fallback_beat_duration / subdivisions_per_beat), 4),
        "total_duration": round(total_duration, 3),
        "meter_numerator": meter_numerator,
        "meter_denominator": meter_denominator,
        "estimated_beat_duration": round(estimated_beat_duration, 4),
    }


def quantize_events_to_grid(events: list[dict[str, Any]], grid: dict[str, Any]) -> list[dict[str, Any]]:
    grid_times = grid["grid_times"]
    if not grid_times:
        return events

    quantized_events: list[dict[str, Any]] = []
    previous_end_index = -1

    for event in events:
        start_index = _nearest_grid_index(event["time"], grid_times)
        end_index = _nearest_grid_index(event["time"] + event["duration"], grid_times)

        detected_gap = float(event["time"]) - (
            float(quantized_events[-1]["detected_time"]) + float(quantized_events[-1]["detected_duration"])
        ) if quantized_events else None

        if (
            previous_end_index >= 0
            and start_index > previous_end_index + 1
            and detected_gap is not None
            and detected_gap <= grid["step_duration"] * 1.25
        ):
            start_index = previous_end_index

        if end_index <= start_index:
            end_index = min(len(grid_times) - 1, start_index + 1)

        quantized_start = grid_times[start_index]
        quantized_end = grid_times[end_index]
        quantized_duration = max(grid["step_duration"], round(quantized_end - quantized_start, 4))

        quantized_event = {
            **event,
            "detected_time": event["time"],
            "detected_duration": event["duration"],
            "time": round(quantized_start, 3),
            "duration": round(quantized_duration, 3),
            "grid_start_index": start_index,
            "grid_end_index": end_index,
        }
        quantized_events.append(quantized_event)
        previous_end_index = end_index

    return quantized_events


def _nearest_grid_index(time_seconds: float, grid_times: list[float]) -> int:
    return min(range(len(grid_times)), key=lambda index: abs(grid_times[index] - time_seconds))


def _median_step(grid_times: list[float], fallback: float) -> float:
    if len(grid_times) < 2:
        return fallback

    intervals = [grid_times[index + 1] - grid_times[index] for index in range(len(grid_times) - 1)]
    valid_intervals = [interval for interval in intervals if interval > 0]

    if not valid_intervals:
        return fallback

    valid_intervals.sort()
    middle = len(valid_intervals) // 2
    if len(valid_intervals) % 2 == 1:
        return valid_intervals[middle]

    return (valid_intervals[middle - 1] + valid_intervals[middle]) / 2
