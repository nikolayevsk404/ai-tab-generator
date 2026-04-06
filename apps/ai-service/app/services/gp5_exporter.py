from __future__ import annotations

import base64
import io
from pathlib import Path

import guitarpro

SEVEN_STRING_TUNING = [
    guitarpro.GuitarString(1, 64),
    guitarpro.GuitarString(2, 59),
    guitarpro.GuitarString(3, 55),
    guitarpro.GuitarString(4, 50),
    guitarpro.GuitarString(5, 45),
    guitarpro.GuitarString(6, 40),
    guitarpro.GuitarString(7, 35),
]


def export_tablature_to_gp5(
    tablature: list[dict],
    source_filename: str,
    title: str = "AI Tab Generator Export",
    tempo: int = 120,
) -> dict[str, str]:
    song = guitarpro.Song(versionTuple=(5, 1, 0), title=title)
    song.tempoName = "Moderate"
    song.tempo = tempo

    track = song.tracks[0]
    track.name = "Generated Guitar"
    track.fretCount = 24
    track.strings = SEVEN_STRING_TUNING

    while len(track.measures) > 1:
        track.measures.pop()
    while len(song.measureHeaders) > 1:
        song.measureHeaders.pop()

    measure_index = 0
    beats_in_measure = 0
    voice = track.measures[0].voices[0]

    for entry in tablature:
        if beats_in_measure == 4:
            measure_index += 1
            beats_in_measure = 0
            voice = _append_measure(song, track).voices[0]

        beat = guitarpro.Beat(voice)
        beat.status = guitarpro.BeatStatus.normal
        beat.duration = guitarpro.Duration(value=4)
        voice.beats.append(beat)

        note = guitarpro.Note(
            beat,
            value=int(entry["fret"]),
            string=int(entry["string"]),
            type=guitarpro.NoteType.normal,
        )
        beat.notes.append(note)
        beats_in_measure += 1

    output = io.BytesIO()
    guitarpro.write(song, output, version=(5, 1, 0))

    base_name = Path(source_filename).stem or "audio-tab"

    return {
        "filename": f"{base_name}.gp5",
        "content_base64": base64.b64encode(output.getvalue()).decode("ascii"),
    }


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
