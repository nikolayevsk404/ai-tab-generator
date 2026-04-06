export type TablatureEntry = {
  time: number
  note: string
  string: number
  fret: number
}

export type AudioJobResponse = {
  job_id: number
  status: 'pending' | 'processing' | 'done' | 'failed'
  filename: string
  result: TablatureEntry[] | null
  logs: {
    detected_frequencies?: Array<{ time: number; frequency: number }>
    detected_notes?: Array<{ time: number; note: string; frequency?: number }>
    raw_segments?: Array<{ time: number; frequency: number }>
  } | null
  error_message: string | null
  created_at: string | null
  updated_at: string | null
}
