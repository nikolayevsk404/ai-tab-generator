import type { AudioJobResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

export async function uploadAudio(file: File): Promise<{ job_id: number; status: string }> {
  const formData = new FormData()
  formData.append('audio', file)

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
    },
    body: formData,
  })

  return parseJsonResponse<{ job_id: number; status: string }>(response, 'Nao foi possivel enviar o audio.')
}

export async function fetchAudioJob(jobId: number): Promise<AudioJobResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${jobId}`, {
    headers: {
      Accept: 'application/json',
    },
  })

  return parseJsonResponse<AudioJobResponse>(response, 'Nao foi possivel consultar o processamento.')
}

async function parseJsonResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  const contentType = response.headers.get('content-type') ?? ''
  const rawBody = await response.text()
  const looksLikeJson = contentType.includes('application/json') || rawBody.trim().startsWith('{') || rawBody.trim().startsWith('[')

  let payload: unknown = null

  if (looksLikeJson && rawBody.trim() !== '') {
    try {
      payload = JSON.parse(rawBody)
    } catch {
      throw new Error(`${fallbackMessage} A API retornou JSON invalido.`)
    }
  }

  if (!response.ok) {
    if (payload && typeof payload === 'object' && 'message' in payload && typeof payload.message === 'string') {
      throw new Error(payload.message)
    }

    if (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string') {
      throw new Error(payload.detail)
    }

    if (!looksLikeJson && rawBody.toLowerCase().includes('<!doctype')) {
      throw new Error(`${fallbackMessage} O servidor retornou uma pagina HTML em vez de JSON, provavelmente por um erro interno na API.`)
    }

    throw new Error(`${fallbackMessage} HTTP ${response.status}.`)
  }

  if (!looksLikeJson) {
    throw new Error(`${fallbackMessage} A API retornou um formato inesperado.`)
  }

  return payload as T
}
