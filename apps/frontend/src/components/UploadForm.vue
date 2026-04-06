<script setup lang="ts">
defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  submit: [file: File]
}>()

function onChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) {
    return
  }

  emit('submit', file)
  input.value = ''
}
</script>

<template>
  <label class="upload-card">
    <input accept=".mp3,.wav" class="upload-input" type="file" :disabled="disabled" @change="onChange" />
    <span class="upload-kicker">Audio to Tab</span>
    <strong>Escolha um .mp3 ou .wav</strong>
    <span>O backend envia para o microservico Python, processa a fila e devolve a tablatura em JSON.</span>
  </label>
</template>
