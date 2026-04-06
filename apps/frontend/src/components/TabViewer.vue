<script setup lang="ts">
import type { TablatureEntry } from '../types'

defineProps<{
  entries: TablatureEntry[]
}>()
</script>

<template>
  <div class="tab-viewer">
    <div class="tab-header">
      <span>Tempo</span>
      <span>Nota</span>
      <span>Corda</span>
      <span>Casa</span>
    </div>

    <div v-for="entry in entries" :key="`${entry.time}-${entry.string}-${entry.fret}`" class="tab-row">
      <span>{{ entry.time.toFixed(3) }}s</span>
      <span>{{ entry.note }}</span>
      <span>{{ entry.string }}</span>
      <span>{{ entry.fret }}</span>
    </div>
  </div>
</template>
