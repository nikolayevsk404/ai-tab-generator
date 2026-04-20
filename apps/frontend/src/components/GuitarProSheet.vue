<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  gp5Url?: string | null
}>()

const mountElement = ref<HTMLElement | null>(null)
const errorMessage = ref('')

type AlphaTabApiInstance = {
  destroy: () => void
  load: (scoreData: unknown) => boolean
  error: { on: (handler: (error: Error) => void) => void }
  renderFinished: { on: (handler: () => void) => void }
}

let api: AlphaTabApiInstance | null = null

const hasSheet = computed(() => Boolean(props.gp5Url))

function destroyViewer() {
  if (api) {
    api.destroy()
    api = null
  }
}

async function renderSheet() {
  destroyViewer()
  errorMessage.value = ''

  if (!mountElement.value || !props.gp5Url) {
    return
  }

  const { AlphaTabApi } = await import('@coderline/alphatab')

  const instance = new AlphaTabApi(mountElement.value, {
    core: {
      engine: 'svg',
      useWorkers: false,
      enableLazyLoading: false,
      fontDirectory: '/alphatab/font/',
    },
    display: {
      layoutMode: 'page',
      barsPerRow: 3,
      scale: 0.95,
      stretchForce: 0.92,
    },
    player: {
      enablePlayer: false,
    },
  })

  instance.error.on((error) => {
    errorMessage.value = error?.message || 'Falha ao renderizar a partitura GP5.'
  })

  instance.renderFinished.on(() => {
    errorMessage.value = ''
  })

  instance.load(props.gp5Url)
  api = instance
}

watch(
  () => props.gp5Url,
  () => {
    void renderSheet()
  },
  { immediate: true },
)

onMounted(() => {
  void renderSheet()
})

onBeforeUnmount(() => {
  destroyViewer()
})
</script>

<template>
  <div class="gp-sheet-viewer">
    <div class="gp-sheet-header card-head result-title-block">
      <div>
        <p class="status-label">Visualizador</p>
        <h2>Guitar Pro</h2>
      </div>
      <div class="result-meta result-meta-placeholder" aria-hidden="true">placeholder</div>
    </div>

    <p v-if="errorMessage" class="error-copy">{{ errorMessage }}</p>

    <div v-show="hasSheet" ref="mountElement" class="gp-sheet-surface"></div>
  </div>
</template>
