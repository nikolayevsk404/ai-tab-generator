export type TablatureEntry = {
  event_id?: number
  time: number
  detected_time?: number
  duration?: number
  note: string
  mapped_note?: string
  string: number
  fret: number
  transposed?: boolean
  event_type?: 'single_note' | 'chord'
  technique?: string | null
}

export type AudioJobResponse = {
  job_id: number
  status: 'pending' | 'processing' | 'done' | 'failed'
  filename: string
  result: TablatureEntry[] | null
  exports: {
    gp5: {
      filename: string
      path: string
    } | null
    gp5_download_url: string | null
  }
  logs: {
    audio_context?: {
      tempo_bpm: number
      beat_times: number[]
      onset_times?: number[]
      guitar_tone: 'clean' | 'distorted' | 'mixed'
      raw_note_event_count?: number
      post_filter_event_count?: number
      detected_string_count?: number
      detected_tuning?: string
      tuning_notes?: Record<number, string>
      distortion_features?: {
        spectral_flatness: number
        zero_crossing_rate: number
        harmonic_ratio: number
        spectral_rolloff?: number
      }
      guitar_presence_score?: number
    }
    detected_frequencies?: Array<{ time: number; frequencies: number[] }>
    detected_notes?: Array<{
      time: number
      duration: number
      notes: string[]
      primary_note: string
      is_chord: boolean
      octave_doubling: boolean
      harmonic_candidate: boolean
    }>
    tab_events?: Array<{
      event_id: number
      time: number
      duration: number
      event_type: 'single_note' | 'chord'
      technique?: string | null
      notes: Array<{ note: string; mapped_note: string; string: number; fret: number; transposed: boolean }>
    }>
    raw_segments?: Array<{
      time: number
      duration: number
      notes: string[]
      is_chord: boolean
      octave_doubling: boolean
      harmonic_candidate: boolean
    }>
    warnings?: Array<{ time: number; note: string; mapped_note?: string; reason: string }>
  } | null
  error_message: string | null
  created_at: string | null
  updated_at: string | null
}
