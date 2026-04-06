import type { AudioJobResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

export async function uploadAudio(file: File): Promise<{ job_id: number; status: string }> {
  const formData = new FormData()
  formData.append('audio', file)

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('Nao foi possivel enviar o audio.')
  }

  return response.json()
}

export async function fetchAudioJob(jobId: number): Promise<AudioJobResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${jobId}`)

  if (!response.ok) {
    throw new Error('Nao foi possivel consultar o processamento.')
  }

  return response.json()
}
