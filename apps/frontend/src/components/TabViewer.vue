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
      <span class="tab-time">{{ entry.time.toFixed(3) }}s</span>
      <span class="tab-note">
        {{ entry.note }}
        <small v-if="entry.event_type === 'chord'">acorde</small>
        <small v-else-if="entry.technique">{{ entry.technique }}</small>
      </span>
      <span class="tab-pill">S{{ entry.string }}</span>
      <span class="tab-fret">{{ entry.fret }}</span>
    </div>
  </div>
</template>
