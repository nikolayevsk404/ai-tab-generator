<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

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
        <p class="eyebrow">Blackened Audio Forge</p>
        <span class="hero-badge">Laravel + Vue + Python</span>
      </div>

      <div class="hero-grid">
        <div class="hero-copy-block">
          <h1>AI Tab Generator</h1>
          <p class="hero-copy">
            Envie o audio do solo, processe na fila e receba uma tablatura com leitura ritmica, mapeamento de braço e export em Guitar Pro.
          </p>

          <div class="hero-meta">
            <div class="meta-card">
              <span>Escopo</span>
              <strong>Solo Guitar</strong>
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
          <p class="status-label">Status</p>
          <strong>{{ activeJob?.status ?? 'idle' }}</strong>
          <span v-if="selectedFileName">{{ selectedFileName }}</span>
          <span v-if="activeJob?.job_id">Job #{{ activeJob.job_id }}</span>
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

      <div class="panel">
        <div class="analysis-grid">
          <div class="result-card">
            <div class="result-heading">
              <h2>Tablatura</h2>
              <div class="result-actions">
                <span v-if="activeJob?.result?.length">{{ activeJob.result.length }} notas</span>
                <a
                  v-if="activeJob?.exports.gp5_download_url"
                  class="download-link"
                  :href="activeJob.exports.gp5_download_url"
                >
                  Baixar .gp5
                </a>
              </div>
            </div>

            <TabViewer v-if="activeJob?.result?.length" :entries="activeJob.result" />
            <p v-else class="empty-copy">
              A tablatura aparece aqui quando o processamento terminar.
            </p>
          </div>

          <div class="logs-card">
            <h2>Logs do pipeline</h2>
            <pre>{{ JSON.stringify(activeJob?.logs ?? {}, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
