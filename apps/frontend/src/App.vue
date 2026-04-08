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
    <section class="hero">
      <p class="eyebrow">Laravel + Vue + Python</p>
      <h1>AI Tab Generator</h1>
      <p class="hero-copy">
        Upload de audio, fila assincrona no backend e pipeline inicial com pitch detection para gerar tablatura de guitarra em JSON.
      </p>
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
          <span v-if="errorMessage" class="error-copy">{{ errorMessage }}</span>
          <span v-if="activeJob?.error_message" class="error-copy">{{ activeJob.error_message }}</span>
        </div>
      </div>

      <div class="panel">
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
    </section>
  </main>
</template>
