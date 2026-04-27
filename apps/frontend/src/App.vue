<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import GuitarProSheet from './components/GuitarProSheet.vue'
import TabViewer from './components/TabViewer.vue'
import UploadForm from './components/UploadForm.vue'
import { fetchAudioJob, uploadAudio } from './services/api'
import type { AudioJobResponse } from './types'

const activeJob = ref<AudioJobResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const selectedFileName = ref('')

let pollTimer: number | undefined

const isProcessing = computed(() =>
  activeJob.value ? ['pending', 'processing'].includes(activeJob.value.status) : false,
)

async function startUpload(file: File) {
  loading.value = true
  errorMessage.value = ''
  selectedFileName.value = file.name

  try {
    const { job_id } = await uploadAudio(file)
    await refreshJob(job_id)
    startPolling(job_id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Falha inesperada no upload.'
  } finally {
    loading.value = false
  }
}

async function refreshJob(jobId: number) {
  activeJob.value = await fetchAudioJob(jobId)

  if (!isProcessing.value) {
    stopPolling()
  }
}

function startPolling(jobId: number) {
  stopPolling()
  pollTimer = window.setInterval(() => {
    void refreshJob(jobId)
  }, 2500)
}

function stopPolling() {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = undefined
  }
}

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <main class="page-shell">
    <section class="hero-frame">
      <div class="hero-topline">
        <p class="eyebrow">DEV BY NIKOLAYEVSK</p>
        <span class="hero-badge">Laravel + Vue + Python</span>
      </div>

      <div class="hero-grid">
        <div class="hero-copy-block">
          <h1>AI Tab Generator</h1>
          <p class="hero-copy">
            Envie o áudio do solo, aguarde o processamento e receba a tablatura com ritmo, mapeamento do braço e exportação para Guitar Pro.
          </p>

          <div class="hero-meta">
            <div class="meta-card">
              <span>Escopo</span>
              <strong>Guitar Solo</strong>
            </div>
            <div class="meta-card">
              <span>Setup</span>
              <strong>6 Strings / Standard</strong>
            </div>
            <div class="meta-card">
              <span>Output</span>
              <strong>JSON + GP5</strong>
            </div>
          </div>
        </div>

        <aside class="hero-sideboard">
          <h2>Transcription Console</h2>
          <ul class="hero-list">
            <li>Upload simples de audio para uma analise automatica focada em solo de guitarra.</li>
            <li>Fila assincrona com deteccao de eventos, filtragem de guitarra e quantizacao ritmica.</li>
            <li>Saida em tablatura visual, logs tecnicos do pipeline e exportacao `.gp5`.</li>
          </ul>
        </aside>
      </div>
    </section>

    <section class="panel-grid">
      <div class="panel">
        <UploadForm :disabled="loading || isProcessing" @submit="startUpload" />

        <div class="status-card">
          <div class="card-head">
            <p class="status-label">Status</p>
            <h2>Painel do Job</h2>
          </div>
          <div class="card-stack">
            <strong class="status-pill">
              <span>{{ activeJob?.status ?? 'idle' }}</span>
              <span v-if="isProcessing" class="status-dots" aria-hidden="true">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </strong>
            <span v-if="selectedFileName">{{ selectedFileName }}</span>
            <span v-if="activeJob?.logs?.audio_context">
              Timbre: {{ activeJob.logs.audio_context.guitar_tone }} | BPM: {{ Math.round(activeJob.logs.audio_context.tempo_bpm) }}
            </span>
            <span v-if="activeJob?.logs?.audio_context?.detected_tuning">
              Setup: {{ activeJob.logs.audio_context.detected_tuning }} | Cordas: {{ activeJob.logs.audio_context.detected_string_count }}
            </span>
            <span v-if="activeJob?.logs?.audio_context?.raw_note_event_count !== undefined">
              Eventos: {{ activeJob.logs.audio_context.post_filter_event_count }} / {{ activeJob.logs.audio_context.raw_note_event_count }}
            </span>
            <span v-if="errorMessage" class="error-copy">{{ errorMessage }}</span>
            <span v-if="activeJob?.error_message" class="error-copy">{{ activeJob.error_message }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="analysis-grid">
          <div class="result-card">
            <div class="card-head result-heading">
              <div class="result-title-block">
                <p class="status-label">Resultado</p>
                <h2>Tablatura</h2>
                <div class="result-meta">
                  <span v-if="activeJob?.logs?.audio_context?.tempo_bpm">
                    BPM {{ Math.round(activeJob.logs.audio_context.tempo_bpm) }}
                  </span>
                  <span v-if="activeJob?.result?.length">{{ activeJob.result.length }} notas</span>
                </div>
              </div>
              <div class="result-actions">
                <a
                  v-if="activeJob?.exports.gp5_download_url"
                  class="download-link"
                  :href="activeJob.exports.gp5_download_url"
                >
                  Baixar .gp5
                </a>
              </div>
            </div>

            <TabViewer
              v-if="activeJob?.result?.length"
              :entries="activeJob.result"
            />
          </div>

          <div class="logs-card">
            <div class="card-head">
              <p class="status-label">Diagnostico</p>
              <h2>Logs do pipeline</h2>
            </div>
            <pre>{{ JSON.stringify(activeJob?.logs ?? {}, null, 2) }}</pre>
          </div>
        </div>

        <div class="sheet-card">
          <GuitarProSheet :gp5-url="activeJob?.exports.gp5_download_url" />
        </div>
      </div>
    </section>
  </main>
</template>
