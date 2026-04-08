from __future__ import annotations

import base64
import io
from pathlib import Path

import guitarpro
from app.services.note_mapper import note_name_to_midi

def export_tablature_to_gp5(
    tab_events: list[dict],
    source_filename: str,
    title: str = "AI Tab Generator Export",
    tempo: int = 120,
    tuning: dict[int, str] | None = None,
    timing_grid: dict | None = None,
) -> dict[str, str]:
    song = guitarpro.Song(versionTuple=(5, 1, 0), title=title)
    song.tempoName = "Lead Solo"
    song.tempo = tempo

    track = song.tracks[0]
    track.name = "Generated Lead Guitar"
    track.fretCount = 24
    track.strings = build_guitar_strings(tuning or {1: "E4", 2: "B3", 3: "G3", 4: "D3", 5: "A2", 6: "E2"})
    song.measureHeaders[0].timeSignature.numerator = int((timing_grid or {}).get("meter_numerator", 4) or 4)
    song.measureHeaders[0].timeSignature.denominator.value = int((timing_grid or {}).get("meter_denominator", 4) or 4)

    while len(track.measures) > 1:
        track.measures.pop()
    while len(song.measureHeaders) > 1:
        song.measureHeaders.pop()

    voice = track.measures[0].voices[0]
    current_measure_index = 0
    timing_grid = timing_grid or {}
    subdivisions_per_beat = int(timing_grid.get("subdivisions_per_beat", 4) or 4)
    slots_per_measure = subdivisions_per_beat * 4
    timeline_items = _build_timeline_items(tab_events, timing_grid)

    slot_cursor = 0

    for item in timeline_items:
        measure_index = slot_cursor // slots_per_measure
        if measure_index > current_measure_index:
            while current_measure_index < measure_index:
                voice = _append_measure(song, track).voices[0]
                current_measure_index += 1

        duration_chunks = _decompose_slot_span(item["slot_span"], subdivisions_per_beat)

        for chunk_slots in duration_chunks:
            beat = guitarpro.Beat(voice)
            beat.status = guitarpro.BeatStatus.normal if item["notes"] else guitarpro.BeatStatus.rest
            beat.duration = _duration_from_slot_span(chunk_slots, subdivisions_per_beat)
            if item.get("technique") == "wah":
                beat.text = "wah"
            voice.beats.append(beat)

            for entry in item["notes"]:
                note = guitarpro.Note(
                    beat,
                    value=int(entry["fret"]),
                    string=int(entry["string"]),
                    type=guitarpro.NoteType.normal,
                )
                _apply_note_effects(note, item.get("technique"))
                beat.notes.append(note)

            slot_cursor += chunk_slots

            new_measure_index = slot_cursor // slots_per_measure
            if new_measure_index > current_measure_index:
                while current_measure_index < new_measure_index:
                    voice = _append_measure(song, track).voices[0]
                    current_measure_index += 1

    output = io.BytesIO()
    guitarpro.write(song, output, version=(5, 1, 0))

    base_name = Path(source_filename).stem or "audio-tab"

    return {
        "filename": f"{base_name}.gp5",
        "content_base64": base64.b64encode(output.getvalue()).decode("ascii"),
    }


def build_guitar_strings(tuning: dict[int, str]) -> list[guitarpro.GuitarString]:
    return [
        guitarpro.GuitarString(string_number, note_name_to_midi(note_name))
        for string_number, note_name in sorted(tuning.items())
    ]


def _append_measure(song: guitarpro.Song, track: guitarpro.Track) -> guitarpro.Measure:
    previous_header = song.measureHeaders[-1]
    measure_length = guitarpro.Duration.quarterTime * previous_header.timeSignature.numerator
    header = guitarpro.MeasureHeader(
        number=previous_header.number + 1,
        start=previous_header.start + measure_length,
    )
    song.measureHeaders.append(header)

    measure = guitarpro.Measure(track, header)
    track.measures.append(measure)
    return measure


def _build_timeline_slots(tab_events: list[dict], timing_grid: dict) -> list[dict]:
    items = _build_timeline_items(tab_events, timing_grid)
    slots: list[dict] = []

    for item in items:
        for _ in range(item["slot_span"]):
            slots.append({"notes": item["notes"]})

    return slots


def _build_timeline_items(tab_events: list[dict], timing_grid: dict) -> list[dict]:
    grid_times = timing_grid.get("grid_times", [])
    if not grid_times:
        items = []
        for event in tab_events:
            items.append({"notes": event["notes"], "slot_span": 1, "technique": event.get("technique")})
        return items

    safe_end_indices = [
        event.get("grid_end_index")
        if event.get("grid_end_index") is not None
        else event.get("grid_start_index", 0)
        for event in tab_events
    ]
    safe_end_indices = [index for index in safe_end_indices if index is not None]
    max_index = max(safe_end_indices, default=0)
    slot_count = max(1, len(grid_times) - 1, max_index)
    event_by_start: dict[int, dict] = {}

    for event in tab_events:
        start_index = event.get("grid_start_index", 0)
        if start_index is None:
            continue
        start_index = int(start_index)
        if 0 <= start_index < slot_count:
            event_by_start[start_index] = event

    items: list[dict] = []
    slot_index = 0

    while slot_index < slot_count:
        if slot_index in event_by_start:
            event = event_by_start[slot_index]
            end_index = event.get("grid_end_index")
            if end_index is None:
                end_index = slot_index + 1
            end_index = max(slot_index + 1, int(end_index))
            items.append(
                {
                    "notes": event["notes"],
                    "slot_span": max(1, end_index - slot_index),
                    "technique": event.get("technique"),
                }
            )
            slot_index = end_index
            continue

        next_event_index = min((index for index in event_by_start.keys() if index > slot_index), default=slot_count)
        rest_span = max(1, next_event_index - slot_index)
        items.append(
            {
                "notes": [],
                "slot_span": rest_span,
                "technique": None,
            }
        )
        slot_index = next_event_index

    return items


def _decompose_slot_span(slot_span: int, subdivisions_per_beat: int) -> list[int]:
    chunks: list[int] = []
    remaining = max(1, slot_span)
    preferred_chunks = _supported_slot_values(subdivisions_per_beat)

    while remaining > 0:
        chunk = max((value for value in preferred_chunks if value <= remaining), default=1)
        chunks.append(chunk)
        remaining -= chunk

    return chunks


def _supported_slot_values(subdivisions_per_beat: int) -> list[int]:
    if subdivisions_per_beat == 8:
        return [32, 24, 16, 12, 8, 6, 4, 3, 2, 1]

    if subdivisions_per_beat == 4:
        return [16, 12, 8, 6, 4, 3, 2, 1]

    if subdivisions_per_beat == 2:
        return [8, 6, 4, 3, 2, 1]

    return [4, 3, 2, 1]


def _duration_from_slot_span(slot_span: int, subdivisions_per_beat: int) -> guitarpro.Duration:
    duration_map = {
        8: {
            1: (32, False),
            2: (16, False),
            3: (16, True),
            4: (8, False),
            6: (8, True),
            8: (4, False),
            12: (4, True),
            16: (2, False),
            24: (2, True),
            32: (1, False),
        },
        4: {
            1: (16, False),
            2: (8, False),
            3: (8, True),
            4: (4, False),
            6: (4, True),
            8: (2, False),
            12: (2, True),
            16: (1, False),
        },
        2: {
            1: (8, False),
            2: (4, False),
            3: (4, True),
            4: (2, False),
            6: (2, True),
            8: (1, False),
        },
    }

    value, dotted = duration_map.get(subdivisions_per_beat, {}).get(slot_span, (16, False))
    return guitarpro.Duration(value=value, isDotted=dotted)


def _apply_note_effects(note: guitarpro.Note, technique: str | None) -> None:
    if technique == "vibrato":
        note.effect.vibrato = True
        return

    if technique == "legato":
        note.effect.hammer = True
        note.effect.letRing = True
        return

    if technique == "harmonic":
        note.effect.harmonic = guitarpro.NaturalHarmonic()
        return

    if technique == "bend":
        note.effect.bend = guitarpro.BendEffect(
            type=guitarpro.BendType.bend,
            value=4,
            points=[
                guitarpro.BendPoint(position=0, value=0),
                guitarpro.BendPoint(position=6, value=4),
                guitarpro.BendPoint(position=12, value=4),
            ],
        )
        return

    if technique == "release_bend":
        note.effect.bend = guitarpro.BendEffect(
            type=guitarpro.BendType.bendRelease,
            value=4,
            points=[
                guitarpro.BendPoint(position=0, value=4),
                guitarpro.BendPoint(position=6, value=4),
                guitarpro.BendPoint(position=12, value=0),
            ],
        )
