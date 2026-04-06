export type TablatureEntry = {
  time: number
  detected_time?: number
  note: string
  mapped_note?: string
  string: number
  fret: number
  transposed?: boolean
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
      guitar_tone: 'clean' | 'distorted' | 'mixed'
      distortion_features?: {
        spectral_flatness: number
        zero_crossing_rate: number
        harmonic_ratio: number
      }
    }
    detected_frequencies?: Array<{ time: number; frequency: number }>
    detected_notes?: Array<{ time: number; quantized_time?: number; note: string; frequency?: number }>
    raw_segments?: Array<{ time: number; frequency: number }>
    warnings?: Array<{ time: number; note: string; mapped_note?: string; reason: string }>
  } | null
  error_message: string | null
  created_at: string | null
  updated_at: string | null
}
