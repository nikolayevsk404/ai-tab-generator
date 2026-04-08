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
    <span class="upload-kicker">Submission</span>
    <strong>Forjar Tablatura de Solo</strong>
    <span>Selecione um `.mp3` ou `.wav`. O backend envia para a fila e o microservico detecta automaticamente o contexto da guitarra para gerar a tab.</span>
    <span class="upload-hint">A IA tenta reconhecer timbre, ritmo e mapeamento do braço sem precisar de configuracao manual.</span>
  </label>
</template>
